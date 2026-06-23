"""Dominio de generación de documentos PDF desde plantillas. Sin HTTP.

Toma una plantilla (su versión publicada, o la última como respaldo) y un proyecto, construye
el contexto, renderiza las secciones a HTML con `render_version`, las envuelve en una página
imprimible y produce el PDF con WeasyPrint (import diferido, igual que `MemoriaService`). Los
bytes se persisten bajo `instance/generated/` y se registra un `GeneratedDocument` con la
versión fijada y el hash SHA-256 del PDF.

Multi-tenant estricto: plantilla, proyecto y documento se comprueban contra la org activa;
lo ajeno responde NotFound (indistinguible de "no existe", evitando IDOR).
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime
from html import escape

from flask import current_app

from app.extensions import db
from app.models.report_template import ReportTemplate, GeneratedDocument
from app.models.organization import OrgBrandingProfile
from app.models.project import Project
from app.errors import NotFound, ValidationError, DomainError
from app.services.template_engine import render_version

logger = logging.getLogger(__name__)

GENERATED_SUBDIR = 'generated'


class DocumentService:

    @staticmethod
    def _accessible_template(org_id, template_id):
        tpl = ReportTemplate.query.get(template_id)
        if not tpl or (tpl.org_id != org_id and not tpl.is_system):
            raise NotFound('Plantilla no encontrada.')
        return tpl

    @staticmethod
    def _owned_project(org_id, project_id):
        project = Project.query.get(project_id)
        if not project or project.org_id != org_id:
            raise NotFound('Proyecto no encontrado.')
        return project

    @staticmethod
    def _owned_document(org_id, doc_id):
        doc = GeneratedDocument.query.get(doc_id)
        if not doc or doc.org_id != org_id:
            raise NotFound('Documento no encontrado.')
        return doc

    @staticmethod
    def _pinned_version(template):
        return template.published_version or template.latest_version

    @staticmethod
    def _branding(org_id):
        try:
            return OrgBrandingProfile.query.filter_by(org_id=org_id).first()
        except Exception:
            return None

    @staticmethod
    def _lang_from_locale(locale):
        return (locale or 'es').split('-')[0].split('_')[0].lower()

    @classmethod
    def _wrap_html(cls, title, sections_html, presentation=None, branding=None):
        safe_title = escape(title or 'Documento')
        presentation = presentation or {}
        lang = cls._lang_from_locale(presentation.get('locale'))
        page_size = presentation.get('page_size') or 'A4'
        color = (branding.primary_color if branding and branding.primary_color else '#1a1a1a')
        safe_color = escape(color, quote=True)
        header = ''
        if branding and branding.logo_path:
            src = escape(branding.logo_path, quote=True)
            header = f'<img class="tpl-logo" src="{src}" alt="">'
        footer = ''
        if branding and branding.footer_text:
            footer = f'<footer class="tpl-footer">{escape(branding.footer_text)}</footer>'
        return (
            f'<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<title>{safe_title}</title>'
            '<style>'
            f'@page {{ size: {page_size}; margin: 2cm; }}'
            'body { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 11pt; '
            'color: #1a1a1a; line-height: 1.5; }'
            f'h1.tpl-doc-title {{ font-size: 18pt; margin: 0 0 1.5em; color: {safe_color}; }}'
            'img.tpl-logo { max-height: 64px; margin: 0 0 1em; }'
            f'section.tpl-section h2 {{ font-size: 13pt; margin: 0 0 0.4em; color: {safe_color}; }}'
            'section.tpl-section { margin-bottom: 1.2em; }'
            '.tpl-body { white-space: normal; }'
            'footer.tpl-footer { margin-top: 2em; font-size: 9pt; color: #666; }'
            '</style></head><body>'
            f'{header}'
            f'<h1 class="tpl-doc-title">{safe_title}</h1>'
            f'{sections_html}'
            f'{footer}'
            '</body></html>'
        )

    @classmethod
    def build_document_html(cls, org_id, template_id, project_id, user=None):
        """Ensambla el HTML imprimible completo y devuelve (html, template, version, project)."""
        template = cls._accessible_template(org_id, template_id)
        project = cls._owned_project(org_id, project_id)
        version = cls._pinned_version(template)
        if version is None:
            raise ValidationError('La plantilla no tiene contenido que generar.')
        presentation = template.presentation
        rendered = render_version(
            version.content, project, user=user, on_error='placeholder',
            presentation=presentation,
        )
        branding = cls._branding(org_id)
        html = cls._wrap_html(template.name, rendered['html'],
                              presentation=presentation, branding=branding)
        return html, template, version, project

    @staticmethod
    def _render_pdf(html):
        from weasyprint import HTML
        return HTML(string=html).write_pdf()

    @staticmethod
    def _generated_dir():
        base = os.path.join(current_app.instance_path, GENERATED_SUBDIR)
        os.makedirs(base, exist_ok=True)
        return base

    @classmethod
    def _persist_pdf(cls, org_id, pdf_bytes):
        org_dir = os.path.join(cls._generated_dir(), str(org_id))
        os.makedirs(org_dir, exist_ok=True)
        filename = f'{uuid.uuid4().hex}.pdf'
        abs_path = os.path.join(org_dir, filename)
        with open(abs_path, 'wb') as handle:
            handle.write(pdf_bytes)
        return os.path.relpath(abs_path, current_app.instance_path)

    @classmethod
    def generate(cls, org_id, template_id, project_id, user=None):
        """Genera y persiste un PDF; crea y devuelve el `GeneratedDocument`."""
        html, template, version, project = cls.build_document_html(
            org_id, template_id, project_id, user=user
        )
        try:
            pdf_bytes = cls._render_pdf(html)
        except Exception as exc:
            logger.exception('WeasyPrint falló al generar el PDF de la plantilla %s', template_id)
            raise DomainError(
                'No se pudo generar el PDF (motor de renderizado no disponible).',
                status_code=500,
            ) from exc

        pdf_path = cls._persist_pdf(org_id, pdf_bytes)
        document = GeneratedDocument(
            org_id=org_id,
            project_id=project.id,
            template_id=template.id,
            template_version_id=version.id,
            kind=template.kind,
            pdf_path=pdf_path,
            pdf_sha256=hashlib.sha256(pdf_bytes).hexdigest(),
            pdf_size_bytes=len(pdf_bytes),
            status='generated',
            generated_by=user.id if user else None,
            generated_at=datetime.utcnow(),
        )
        db.session.add(document)
        db.session.commit()
        return document

    @classmethod
    def list_for_project(cls, org_id, project_id):
        cls._owned_project(org_id, project_id)
        rows = GeneratedDocument.query.filter_by(
            org_id=org_id, project_id=project_id
        ).order_by(GeneratedDocument.generated_at.desc()).all()
        return [d.to_dict() for d in rows]

    @classmethod
    def get_document(cls, org_id, doc_id):
        return cls._owned_document(org_id, doc_id)

    @classmethod
    def read_pdf_bytes(cls, org_id, doc_id):
        """Devuelve (document, pdf_bytes) validando propiedad por org."""
        doc = cls._owned_document(org_id, doc_id)
        abs_path = os.path.join(current_app.instance_path, doc.pdf_path)
        if not os.path.isfile(abs_path):
            raise NotFound('El archivo del documento no está disponible.')
        with open(abs_path, 'rb') as handle:
            return doc, handle.read()

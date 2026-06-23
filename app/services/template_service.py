"""Dominio de plantillas de documentos. Sin HTTP.

Reglas de propiedad (espejo de CatalogService):
- Plantilla con org_id NULL + scope 'system' -> banco oficial (solo lectura; instalable).
- Plantilla con org_id -> propiedad del workspace (CRUD por sus admins).
- Biblioteca de una org = sus TemplateInstallation (plantillas seleccionadas).

Multi-tenant estricto: cada lectura/escritura comprueba que el recurso pertenece a la org
activa; lo ajeno responde NotFound (no se distingue de "no existe", evitando IDOR).
"""

import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.report_template import (
    ReportTemplate, TemplateVersion, TemplateCategory, Label,
    TemplateInstallation, InstallationLabel, DocumentKind,
    TEMPLATE_STATUSES,
)
from app.models.project import Project
from app.errors import NotFound, ValidationError, Forbidden
from app.services.template_engine import render_version, render_text
from app.services.template_engine.context import build_context, ContextResolver

logger = logging.getLogger(__name__)


class TemplateService:

    @staticmethod
    def _owned_template(org_id, template_id):
        tpl = ReportTemplate.query.get(template_id)
        if not tpl or tpl.org_id != org_id:
            raise NotFound('Plantilla no encontrada en tu workspace.')
        return tpl

    @staticmethod
    def _accessible_template(org_id, template_id):
        tpl = ReportTemplate.query.get(template_id)
        if not tpl or (tpl.org_id != org_id and not tpl.is_system):
            raise NotFound('Plantilla no encontrada.')
        return tpl

    @classmethod
    def list_org_templates(cls, org_id, kind=None):
        query = ReportTemplate.query.filter(ReportTemplate.org_id == org_id)
        if kind:
            query = query.filter(ReportTemplate.kind == kind)
        return [t.to_dict() for t in query.order_by(ReportTemplate.name).all()]

    @staticmethod
    def list_system_bank(kind=None):
        query = ReportTemplate.query.filter(
            ReportTemplate.org_id.is_(None), ReportTemplate.scope == 'system'
        )
        if kind:
            query = query.filter(ReportTemplate.kind == kind)
        return [t.to_dict() for t in query.order_by(ReportTemplate.name).all()]

    @classmethod
    def get_template(cls, org_id, template_id):
        return cls._accessible_template(org_id, template_id).to_dict(with_content=True)

    @staticmethod
    def _validate_kind(kind):
        if kind not in DocumentKind.ALL:
            raise ValidationError(
                f"Tipo de documento inválido. Válidos: {', '.join(DocumentKind.ALL)}"
            )

    @classmethod
    def create_template(cls, org_id, created_by, kind, name, description='',
                         country=None, region=None, content=None,
                         locale=None, currency=None, required_by=None, stage=None):
        cls._validate_kind(kind)
        if not name or not name.strip():
            raise ValidationError('El nombre es obligatorio.')
        tpl = ReportTemplate(
            org_id=org_id, scope='org', kind=kind, name=name.strip(),
            description=(description or '').strip(), country=country, region=region,
            locale=locale, currency=currency, required_by=required_by, stage=stage,
            status='draft', is_official=False, created_by=created_by,
        )
        db.session.add(tpl)
        db.session.flush()
        version = TemplateVersion(template_id=tpl.id, version=1, changelog='Versión inicial')
        version.content = content if content is not None else []
        db.session.add(version)
        db.session.commit()
        return tpl

    @classmethod
    def update_template(cls, org_id, template_id, **fields):
        tpl = cls._owned_template(org_id, template_id)
        for attr in ('name', 'description', 'country', 'region', 'thumbnail_path',
                     'locale', 'currency', 'required_by', 'stage'):
            if attr in fields and fields[attr] is not None:
                setattr(tpl, attr, fields[attr])
        if 'status' in fields and fields['status'] is not None:
            if fields['status'] not in TEMPLATE_STATUSES:
                raise ValidationError(
                    f"Estado inválido. Válidos: {', '.join(TEMPLATE_STATUSES)}"
                )
            tpl.status = fields['status']
        db.session.commit()
        return tpl

    @classmethod
    def delete_template(cls, org_id, template_id):
        tpl = cls._owned_template(org_id, template_id)
        TemplateInstallation.query.filter_by(template_id=tpl.id).delete()
        db.session.delete(tpl)
        db.session.commit()

    @classmethod
    def save_content(cls, org_id, template_id, content, changelog=''):
        tpl = cls._owned_template(org_id, template_id)
        cls.validate_content(content)
        latest = tpl.latest_version
        next_version = (latest.version + 1) if latest else 1
        version = TemplateVersion(
            template_id=tpl.id, version=next_version, changelog=(changelog or '')
        )
        version.content = content
        db.session.add(version)
        db.session.commit()
        return version

    @classmethod
    def publish(cls, org_id, template_id):
        tpl = cls._owned_template(org_id, template_id)
        latest = tpl.latest_version
        if not latest:
            raise ValidationError('La plantilla no tiene contenido que publicar.')
        latest.published_at = datetime.utcnow()
        tpl.status = 'published'
        db.session.commit()
        return tpl

    @staticmethod
    def validate_content(content):
        if not isinstance(content, list):
            raise ValidationError('El contenido debe ser una lista de secciones.')
        resolver = ContextResolver({
            'project': None, 'panel': None, 'inverter': None, 'battery': None,
            'wire': None, 'user': None, 'org': None, 'finance': None,
        })
        for idx, section in enumerate(content):
            if not isinstance(section, dict):
                raise ValidationError(f'La sección {idx} no es un objeto válido.')
            for text in (section.get('title') or '', section.get('body') or ''):
                try:
                    render_text(text, resolver, on_error='raise')
                except Exception as exc:
                    raise ValidationError(
                        f'Expresión inválida en la sección {idx}: {exc}'
                    )

    @classmethod
    def preview(cls, org_id, template_id, project_id, user=None):
        tpl = cls._accessible_template(org_id, template_id)
        project = Project.query.get(project_id)
        if not project or project.org_id != org_id:
            raise NotFound('Proyecto no encontrado.')
        latest = tpl.latest_version
        content = latest.content if latest else []
        return render_version(content, project, user=user, on_error='placeholder')

    @classmethod
    def list_library(cls, org_id, favorite=None, category_id=None):
        query = TemplateInstallation.query.filter(TemplateInstallation.org_id == org_id)
        if favorite is not None:
            query = query.filter(TemplateInstallation.is_favorite.is_(favorite))
        if category_id is not None:
            query = query.filter(TemplateInstallation.category_id == category_id)
        return [i.to_dict() for i in query.order_by(TemplateInstallation.added_at.desc()).all()]

    @classmethod
    def install(cls, org_id, template_id):
        cls._accessible_template(org_id, template_id)
        existing = TemplateInstallation.query.filter_by(
            org_id=org_id, template_id=template_id
        ).first()
        if existing:
            return existing
        installation = TemplateInstallation(
            org_id=org_id, template_id=template_id, added_at=datetime.utcnow()
        )
        db.session.add(installation)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            installation = TemplateInstallation.query.filter_by(
                org_id=org_id, template_id=template_id
            ).first()
        return installation

    @classmethod
    def _owned_installation(cls, org_id, installation_id):
        inst = TemplateInstallation.query.get(installation_id)
        if not inst or inst.org_id != org_id:
            raise NotFound('Instalación no encontrada en tu biblioteca.')
        return inst

    @classmethod
    def uninstall(cls, org_id, installation_id):
        inst = cls._owned_installation(org_id, installation_id)
        InstallationLabel.query.filter_by(installation_id=inst.id).delete()
        db.session.delete(inst)
        db.session.commit()

    @classmethod
    def set_favorite(cls, org_id, installation_id, is_favorite):
        inst = cls._owned_installation(org_id, installation_id)
        inst.is_favorite = bool(is_favorite)
        db.session.commit()
        return inst

    @classmethod
    def set_category(cls, org_id, installation_id, category_id):
        inst = cls._owned_installation(org_id, installation_id)
        if category_id is not None:
            category = TemplateCategory.query.get(category_id)
            if not category or category.org_id != org_id:
                raise NotFound('Categoría no encontrada en tu workspace.')
        inst.category_id = category_id
        db.session.commit()
        return inst

    @classmethod
    def set_labels(cls, org_id, installation_id, label_ids):
        inst = cls._owned_installation(org_id, installation_id)
        InstallationLabel.query.filter_by(installation_id=inst.id).delete()
        for label_id in set(label_ids or []):
            label = Label.query.get(label_id)
            if not label or label.org_id != org_id:
                raise NotFound('Etiqueta no encontrada en tu workspace.')
            db.session.add(InstallationLabel(installation_id=inst.id, label_id=label_id))
        db.session.commit()
        db.session.refresh(inst)
        return inst

    @staticmethod
    def list_categories(org_id):
        rows = TemplateCategory.query.filter_by(org_id=org_id).order_by(
            TemplateCategory.name).all()
        return [c.to_dict() for c in rows]

    @staticmethod
    def create_category(org_id, name):
        if not name or not name.strip():
            raise ValidationError('El nombre de la categoría es obligatorio.')
        category = TemplateCategory(org_id=org_id, name=name.strip())
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValidationError('Ya existe una categoría con ese nombre.')
        return category

    @classmethod
    def delete_category(cls, org_id, category_id):
        category = TemplateCategory.query.get(category_id)
        if not category or category.org_id != org_id:
            raise NotFound('Categoría no encontrada en tu workspace.')
        TemplateInstallation.query.filter_by(category_id=category.id).update(
            {'category_id': None})
        db.session.delete(category)
        db.session.commit()

    @staticmethod
    def list_labels(org_id):
        rows = Label.query.filter_by(org_id=org_id).order_by(Label.name).all()
        return [l.to_dict() for l in rows]

    @staticmethod
    def create_label(org_id, name):
        if not name or not name.strip():
            raise ValidationError('El nombre de la etiqueta es obligatorio.')
        label = Label(org_id=org_id, name=name.strip())
        db.session.add(label)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValidationError('Ya existe una etiqueta con ese nombre.')
        return label

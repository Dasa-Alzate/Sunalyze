"""Servicio de plantillas de correo: renderiza y (en dev) registra el envio.

Locale-aware: la plantilla y el asunto se resuelven por el locale del
destinatario, con fallback a `es` (base actual). Las plantillas viven en
`templates/emails/<locale>/<archivo>`; hoy solo existe `es`, quedando el hueco
para `en` sin traducir todo aun.
"""

import logging
from jinja2 import TemplateNotFound
from flask import render_template

from app.i18n import DEFAULT_LOCALE, normalize_locale

logger = logging.getLogger(__name__)


class EmailService:
    """Renderizador de plantillas de email transaccional.

    Encapsula el catalogo de plantillas (asunto por locale + fichero Jinja). El
    envio real se delegaria a un proveedor (SMTP/SES/etc.); en desarrollo solo se
    registra en el log para no acoplar la app a credenciales externas.
    """

    TEMPLATES = {
        'welcome': {'file': 'welcome.html'},
        'reset-password': {'file': 'reset-password.html'},
        'memoria-ready': {'file': 'memoria-ready.html'},
        'invitation': {'file': 'invitation.html'},
    }

    SUBJECTS = {
        'es': {
            'welcome': 'Bienvenido a Sunalyze',
            'reset-password': 'Restablece tu contraseña',
            'memoria-ready': 'Tu memoria técnica está lista',
            'invitation': 'Te han invitado a un equipo en Sunalyze',
        },
    }

    @classmethod
    def _locale(cls, locale):
        return normalize_locale(locale) or DEFAULT_LOCALE

    @classmethod
    def subject_for(cls, template_id, locale=None):
        loc = cls._locale(locale)
        table = cls.SUBJECTS.get(loc) or cls.SUBJECTS[DEFAULT_LOCALE]
        if template_id not in table:
            table = cls.SUBJECTS[DEFAULT_LOCALE]
        return table[template_id]

    @classmethod
    def catalog(cls, locale=None):
        return [
            {'id': tid, 'subject': cls.subject_for(tid, locale)}
            for tid in cls.TEMPLATES
        ]

    @classmethod
    def render(cls, template_id, context=None, locale=None):
        meta = cls.TEMPLATES.get(template_id)
        if not meta:
            raise KeyError(template_id)
        loc = cls._locale(locale)
        candidates = [f'emails/{loc}/{meta["file"]}']
        if loc != DEFAULT_LOCALE:
            candidates.append(f'emails/{DEFAULT_LOCALE}/{meta["file"]}')
        for path in candidates:
            try:
                html = render_template(path, **(context or {}))
                break
            except TemplateNotFound:
                continue
        else:
            raise KeyError(template_id)
        return {'subject': cls.subject_for(template_id, loc), 'html': html, 'locale': loc}

    @classmethod
    def send(cls, template_id, to, context=None, locale=None):
        rendered = cls.render(template_id, context, locale=locale)
        logger.info(
            "EMAIL (dev, no enviado) to=%s locale=%s subject=%s bytes=%d",
            to, rendered['locale'], rendered['subject'], len(rendered['html']),
        )
        return {
            'sent': False, 'to': to, 'subject': rendered['subject'],
            'locale': rendered['locale'], 'reason': 'SMTP no configurado (dev)',
        }

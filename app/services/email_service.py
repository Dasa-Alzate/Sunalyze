"""Servicio de plantillas de correo: renderiza y delega el envio al backend activo.

Locale-aware: la plantilla y el asunto se resuelven por el locale del
destinatario, con fallback a `es` (base actual). Las plantillas viven en
`templates/emails/<locale>/<archivo>`; hoy solo existe `es`, quedando el hueco
para `en` sin traducir todo aun.

El envio real lo hace el `MailGateway` seleccionado por `MAIL_BACKEND` (`log` por
defecto: solo registra; `smtp`: entrega real). El contrato de `send` es blando: un
fallo del backend nunca propaga al llamador (el registro o el reset no deben caer
porque el SMTP este caido); se loguea como error y se devuelve `sent=False`.
"""

import logging
from jinja2 import TemplateNotFound
from flask import render_template, current_app

from app.gateways.mail import get_mailer
from app.i18n import DEFAULT_LOCALE, normalize_locale

logger = logging.getLogger(__name__)


class EmailService:
    """Renderizador de plantillas de email transaccional.

    Encapsula el catalogo de plantillas (asunto por locale + fichero Jinja). El
    envio se delega al `MailGateway` activo: `log` en desarrollo (solo registra,
    sin credenciales externas) o `smtp` en produccion.
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
        try:
            outcome = get_mailer().send(
                to, rendered['subject'], rendered['html'], locale=rendered['locale'],
            )
        except Exception:
            logger.error(
                "Fallo al enviar email template=%s to=%s backend=%s",
                template_id, to, current_app.config.get('MAIL_BACKEND', 'log'),
                exc_info=True,
            )
            outcome = {'sent': False, 'reason': 'Fallo del backend de correo (ver logs)'}
        return {
            'to': to, 'subject': rendered['subject'], 'locale': rendered['locale'],
            **outcome,
        }

"""Servicio de plantillas de correo: renderiza y (en dev) registra el envio."""

import logging
from flask import render_template

logger = logging.getLogger(__name__)


class EmailService:
    """Renderizador de plantillas de email transaccional.

    Encapsula el catalogo de plantillas (asunto + fichero Jinja). El envio
    real se delegaria a un proveedor (SMTP/SES/etc.); en desarrollo solo se
    registra en el log para no acoplar la app a credenciales externas.
    """

    TEMPLATES = {
        'welcome': {'subject': 'Bienvenido a Sunalyze', 'template': 'emails/welcome.html'},
        'reset-password': {'subject': 'Restablece tu contraseña', 'template': 'emails/reset-password.html'},
        'memoria-ready': {'subject': 'Tu memoria técnica está lista', 'template': 'emails/memoria-ready.html'},
        'invitation': {'subject': 'Te han invitado a un equipo en Sunalyze', 'template': 'emails/invitation.html'},
    }

    @classmethod
    def catalog(cls):
        return [{'id': tid, 'subject': meta['subject']} for tid, meta in cls.TEMPLATES.items()]

    @classmethod
    def render(cls, template_id, context=None):
        meta = cls.TEMPLATES.get(template_id)
        if not meta:
            raise KeyError(template_id)
        html = render_template(meta['template'], **(context or {}))
        return {'subject': meta['subject'], 'html': html}

    @classmethod
    def send(cls, template_id, to, context=None):
        rendered = cls.render(template_id, context)
        logger.info(
            "EMAIL (dev, no enviado) to=%s subject=%s bytes=%d",
            to, rendered['subject'], len(rendered['html']),
        )
        return {'sent': False, 'to': to, 'subject': rendered['subject'], 'reason': 'SMTP no configurado (dev)'}

"""Adaptador de correo que solo registra (DEFAULT).

Replica exacto el comportamiento histórico de `EmailService.send`: escribe la
línea de log de desarrollo y marca el mensaje como no enviado, sin acoplar la app
a credenciales externas.
"""

import logging

from app.gateways.mail.base import MailGateway

logger = logging.getLogger(__name__)


class LogMail(MailGateway):
    """Registra el correo en el log en lugar de enviarlo."""

    def send(self, to, subject, html, locale=None):
        logger.info(
            "EMAIL (dev, no enviado) to=%s locale=%s subject=%s bytes=%d",
            to, locale, subject, len(html),
        )
        return {'sent': False, 'reason': 'SMTP no configurado (dev)'}

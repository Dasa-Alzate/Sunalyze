
import logging

from app.gateways.mail.base import MailGateway

logger = logging.getLogger(__name__)


class LogMail(MailGateway):

    def send(self, to, subject, html, locale=None):
        logger.info(
            "EMAIL (dev, no enviado) to=%s locale=%s subject=%s bytes=%d",
            to, locale, subject, len(html),
        )
        return {'sent': False, 'reason': 'SMTP no configurado (dev)'}

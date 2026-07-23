
from flask import current_app

from app.gateways.mail.base import MailGateway, MailError
from app.gateways.mail.log import LogMail

__all__ = ['MailGateway', 'MailError', 'LogMail', 'get_mailer']


def get_mailer():
    backend = (current_app.config.get('MAIL_BACKEND') or 'log').lower()
    if backend == 'smtp':
        from app.gateways.mail.smtp import SMTPMail

        return SMTPMail.from_config(current_app.config)
    return LogMail()

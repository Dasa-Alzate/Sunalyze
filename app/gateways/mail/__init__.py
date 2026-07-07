"""Selección del backend de correo por configuración.

`get_mailer()` devuelve el adaptador indicado por `MAIL_BACKEND` (`log` por defecto,
que solo registra). Un valor desconocido ya rompió el arranque en `config.py`, así que
aquí solo se distingue `smtp` del default. El adaptador SMTP se importa perezosamente,
igual que hacen los selectores de storage y cola.
"""

from flask import current_app

from app.gateways.mail.base import MailGateway, MailError
from app.gateways.mail.log import LogMail

__all__ = ['MailGateway', 'MailError', 'LogMail', 'get_mailer']


def get_mailer():
    """Devuelve el `MailGateway` configurado para la app activa."""
    backend = (current_app.config.get('MAIL_BACKEND') or 'log').lower()
    if backend == 'smtp':
        from app.gateways.mail.smtp import SMTPMail

        return SMTPMail.from_config(current_app.config)
    return LogMail()

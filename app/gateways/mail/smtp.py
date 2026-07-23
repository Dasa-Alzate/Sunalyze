
import smtplib
from email.message import EmailMessage

from app.gateways.mail.base import MailGateway, MailError


class SMTPMail(MailGateway):

    def __init__(self, host, port, username, password, starttls, sender, timeout):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.starttls = starttls
        self.sender = sender
        self.timeout = timeout

    @classmethod
    def from_config(cls, config):
        return cls(
            host=config['MAIL_SMTP_HOST'],
            port=int(config.get('MAIL_SMTP_PORT') or 587),
            username=config.get('MAIL_SMTP_USERNAME') or None,
            password=config.get('MAIL_SMTP_PASSWORD') or None,
            starttls=bool(config.get('MAIL_SMTP_STARTTLS', True)),
            sender=config['MAIL_FROM'],
            timeout=int(config.get('MAIL_TIMEOUT') or 10),
        )

    def _build_message(self, to, subject, html):
        message = EmailMessage()
        message['From'] = self.sender
        message['To'] = to
        message['Subject'] = subject
        message.set_content(html, subtype='html')
        return message

    def send(self, to, subject, html, locale=None):
        message = self._build_message(to, subject, html)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as smtp:
                if self.starttls:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise MailError(f'{type(exc).__name__}: {exc}') from exc
        return {'sent': True}

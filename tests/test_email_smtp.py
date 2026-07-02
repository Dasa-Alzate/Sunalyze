"""Backend de correo SMTP: mensaje correcto, TLS/login y contrato blando.

Con un fake de `smtplib.SMTP` (sin red ni envío real) verifica que el adaptador
SMTP construye el mensaje con from/to/subject/cuerpo correctos, que STARTTLS y
login se invocan según configuración, que un fallo SMTP no propaga excepción a
los llamadores de `EmailService.send`, que el backend `log` sigue siendo el
default sin cambios y que la validación de config rechaza backends desconocidos.
"""

import os
import smtplib
import unittest
from unittest import mock

import config as config_module
from app import create_app
from app.gateways.mail import get_mailer, LogMail
from app.gateways.mail.base import MailError
from app.gateways.mail.smtp import SMTPMail
from app.services.email_service import EmailService


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.calls = []
        self.messages = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.calls.append('starttls')

    def login(self, username, password):
        self.calls.append(('login', username, password))

    def send_message(self, message):
        self.calls.append('send_message')
        self.messages.append(message)


class FailingSMTP(FakeSMTP):
    def send_message(self, message):
        raise smtplib.SMTPException('boom')


class RefusedSMTP(FakeSMTP):
    def __init__(self, host, port, timeout=None):
        super().__init__(host, port, timeout=timeout)
        raise ConnectionRefusedError('conexion rechazada')


SMTP_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite://',
    'TESTING': True,
    'MAIL_BACKEND': 'smtp',
    'MAIL_SMTP_HOST': 'smtp.test.local',
    'MAIL_SMTP_PORT': 2587,
    'MAIL_SMTP_USERNAME': 'ses-user',
    'MAIL_SMTP_PASSWORD': 'ses-pass',
    'MAIL_SMTP_STARTTLS': True,
    'MAIL_FROM': 'Sunalyze <no-reply@sunalyze.test>',
    'MAIL_TIMEOUT': 5,
}


def _make_app(extra=None):
    overrides = {'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True}
    overrides.update(extra or {})
    return create_app(overrides)


class SMTPAdapterTest(unittest.TestCase):
    def setUp(self):
        FakeSMTP.instances = []
        self.app = _make_app(SMTP_CONFIG)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_builds_and_sends_correct_message(self):
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', FakeSMTP):
            result = EmailService.send(
                'welcome', 'ana@example.com',
                {'first_name': 'Ana', 'cta_url': 'https://sunalyze.test/verificar?token=t'},
                locale='es',
            )
        self.assertTrue(result['sent'])
        self.assertEqual(result['to'], 'ana@example.com')
        self.assertEqual(result['subject'], 'Bienvenido a Sunalyze')
        self.assertNotIn('reason', result)
        self.assertEqual(len(FakeSMTP.instances), 1)
        conn = FakeSMTP.instances[0]
        self.assertEqual(conn.host, 'smtp.test.local')
        self.assertEqual(conn.port, 2587)
        self.assertEqual(conn.timeout, 5)
        message = conn.messages[0]
        self.assertEqual(message['From'], 'Sunalyze <no-reply@sunalyze.test>')
        self.assertEqual(message['To'], 'ana@example.com')
        self.assertEqual(message['Subject'], 'Bienvenido a Sunalyze')
        self.assertEqual(message.get_content_type(), 'text/html')
        self.assertIn('Sunalyze', message.get_content())

    def test_starttls_and_login_order(self):
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', FakeSMTP):
            EmailService.send('welcome', 'ana@example.com', {'first_name': 'Ana'})
        self.assertEqual(
            FakeSMTP.instances[0].calls,
            ['starttls', ('login', 'ses-user', 'ses-pass'), 'send_message'],
        )

    def test_without_starttls_and_anonymous_skips_both(self):
        self.app.config.update(
            MAIL_SMTP_STARTTLS=False, MAIL_SMTP_USERNAME=None, MAIL_SMTP_PASSWORD=None,
        )
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', FakeSMTP):
            EmailService.send('welcome', 'ana@example.com', {'first_name': 'Ana'})
        self.assertEqual(FakeSMTP.instances[0].calls, ['send_message'])

    def test_adapter_raises_mail_error_on_smtp_failure(self):
        mailer = get_mailer()
        self.assertIsInstance(mailer, SMTPMail)
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', FailingSMTP):
            with self.assertRaises(MailError):
                mailer.send('ana@example.com', 'Asunto', '<p>Hola</p>')

    def test_smtp_failure_does_not_propagate_to_caller(self):
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', FailingSMTP):
            with self.assertLogs('app.services.email_service', level='ERROR') as captured:
                result = EmailService.send('welcome', 'ana@example.com', {'first_name': 'Ana'})
        self.assertFalse(result['sent'])
        self.assertIn('reason', result)
        self.assertIn('template=welcome', captured.output[0])
        self.assertIn('backend=smtp', captured.output[0])

    def test_connection_refused_does_not_propagate_to_caller(self):
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP', RefusedSMTP):
            with self.assertLogs('app.services.email_service', level='ERROR'):
                result = EmailService.send('welcome', 'ana@example.com', {'first_name': 'Ana'})
        self.assertFalse(result['sent'])


class LogBackendDefaultTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_default_backend_is_log(self):
        self.assertIsInstance(get_mailer(), LogMail)

    def test_log_backend_keeps_legacy_contract(self):
        with mock.patch('app.gateways.mail.smtp.smtplib.SMTP') as smtp_cls:
            with self.assertLogs('app.gateways.mail.log', level='INFO') as captured:
                result = EmailService.send('welcome', 'ana@example.com', {'first_name': 'Ana'})
        smtp_cls.assert_not_called()
        self.assertEqual(result['sent'], False)
        self.assertEqual(result['to'], 'ana@example.com')
        self.assertEqual(result['subject'], 'Bienvenido a Sunalyze')
        self.assertEqual(result['locale'], 'es')
        self.assertEqual(result['reason'], 'SMTP no configurado (dev)')
        self.assertIn('EMAIL (dev, no enviado)', captured.output[0])


class MailConfigValidationTest(unittest.TestCase):
    def test_unknown_backend_fails_at_startup(self):
        with mock.patch.dict(os.environ, {'MAIL_BACKEND': 'smpt'}):
            with self.assertRaises(RuntimeError) as ctx:
                config_module._resolve_mail_backend()
        self.assertIn('MAIL_BACKEND', str(ctx.exception))

    def test_smtp_backend_requires_host_and_from(self):
        env = {'MAIL_BACKEND': 'smtp', 'MAIL_SMTP_HOST': '', 'MAIL_FROM': ''}
        with mock.patch.dict(os.environ, env):
            with self.assertRaises(RuntimeError) as ctx:
                config_module._resolve_mail_backend()
        self.assertIn('MAIL_SMTP_HOST', str(ctx.exception))
        self.assertIn('MAIL_FROM', str(ctx.exception))

    def test_smtp_backend_valid_when_complete(self):
        env = {
            'MAIL_BACKEND': 'smtp',
            'MAIL_SMTP_HOST': 'smtp.test.local',
            'MAIL_FROM': 'no-reply@sunalyze.test',
        }
        with mock.patch.dict(os.environ, env):
            self.assertEqual(config_module._resolve_mail_backend(), 'smtp')

    def test_default_is_log(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('MAIL_BACKEND', None)
            self.assertEqual(config_module._resolve_mail_backend(), 'log')


if __name__ == '__main__':
    unittest.main()

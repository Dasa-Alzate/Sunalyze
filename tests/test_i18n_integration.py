"""Tests de la fase backend de i18n: persistencia y exposicion de user.locale,
resolucion de locale por precedencia (user > Accept-Language > es), codigos de
error estables en la API (code + message), emails locale-aware y no-regresion de
auth/errores existentes.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.errors import (
    DomainError, NotFound, Unauthorized, Forbidden, Conflict, ValidationError,
)
from app.i18n import resolve_locale, normalize_locale
from app.services.email_service import EmailService


def _make_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://',
                      WTF_CSRF_ENABLED=False, IS_PRODUCTION=False)
    return app


class _Base(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed(self):
        self.org = Organization(nombre='Org', type='PERSONAL', plan='free', seats=1)
        db.session.add(self.org)
        db.session.flush()
        self.user = User(email='u@x.com', first_name='U', last_name='U', email_verified=True)
        self.user.set_password('Secret-pass-2026')
        db.session.add(self.user)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=self.org.id, role='owner'))
        db.session.commit()


class LocaleFieldTest(_Base):
    def test_default_locale_is_es(self):
        self.assertEqual(self.user.locale, 'es')

    def test_locale_persists(self):
        self.user.locale = 'en'
        db.session.commit()
        db.session.expire_all()
        again = User.query.get(self.user.id)
        self.assertEqual(again.locale, 'en')

    def test_to_dict_exposes_locale(self):
        self.assertEqual(self.user.to_dict()['locale'], 'es')


class ResolveLocaleTest(_Base):
    def test_normalize_reduces_region(self):
        self.assertEqual(normalize_locale('es-ES'), 'es')
        self.assertEqual(normalize_locale('en_US'), 'en')
        self.assertIsNone(normalize_locale('fr'))

    def test_user_locale_takes_precedence(self):
        self.user.locale = 'en'
        with self.app.test_request_context(headers={'Accept-Language': 'es-ES'}):
            self.assertEqual(resolve_locale(self.user), 'en')

    def test_accept_language_when_no_user(self):
        with self.app.test_request_context(headers={'Accept-Language': 'en-GB,en;q=0.9'}):
            self.assertEqual(resolve_locale(None), 'en')

    def test_default_es_when_nothing(self):
        with self.app.test_request_context():
            self.assertEqual(resolve_locale(None), 'es')

    def test_unsupported_header_falls_back_to_default(self):
        with self.app.test_request_context(headers={'Accept-Language': 'fr-FR'}):
            self.assertEqual(resolve_locale(None), 'es')


class ErrorCodeTest(_Base):
    def test_each_class_has_code_and_message(self):
        cases = [
            (NotFound('x'), 'error.not_found', 404),
            (Unauthorized('x'), 'error.unauthorized', 401),
            (Forbidden('x'), 'error.forbidden', 403),
            (Conflict('x'), 'error.conflict', 409),
            (ValidationError('x'), 'error.validation', 422),
            (DomainError('x'), 'error.bad_request', 400),
        ]
        for err, code, status in cases:
            body = err.to_dict()
            self.assertEqual(body['code'], code)
            self.assertEqual(body['error'], 'x')
            self.assertEqual(err.status_code, status)

    def test_explicit_code_overrides_class_default(self):
        err = Unauthorized('Correo o contraseña incorrectos.', code='auth.invalid_credentials')
        body = err.to_dict()
        self.assertEqual(body['code'], 'auth.invalid_credentials')
        self.assertEqual(body['error'], 'Correo o contraseña incorrectos.')

    def test_handler_emits_code_for_login_failure(self):
        client = self.app.test_client()
        r = client.post('/api/auth/login', json={'email': 'u@x.com', 'password': 'wrong'})
        self.assertEqual(r.status_code, 401)
        body = r.get_json()
        self.assertEqual(body['code'], 'auth.invalid_credentials')
        self.assertIn('error', body)

    def test_handler_emits_code_for_duplicate_register(self):
        client = self.app.test_client()
        r = client.post('/api/auth/register', json={
            'email': 'u@x.com', 'password': 'Secret-pass-2026', 'first_name': 'U',
        })
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()['code'], 'auth.email_taken')


class EmailLocaleTest(_Base):
    def test_renders_default_es(self):
        out = EmailService.render('welcome', {'first_name': 'Ana'})
        self.assertEqual(out['locale'], 'es')
        self.assertEqual(out['subject'], 'Bienvenido a Sunalyze')
        self.assertIn('Sunalyze', out['html'])

    def test_recipient_locale_used(self):
        out = EmailService.send('welcome', 'a@x.com', {'first_name': 'Ana'}, locale='es')
        self.assertEqual(out['locale'], 'es')

    def test_unknown_locale_falls_back_to_es(self):
        out = EmailService.render('reset-password', {'reset_url': '#'}, locale='fr')
        self.assertEqual(out['locale'], 'es')
        self.assertIn('contraseña', out['html'])

    def test_en_falls_back_to_es_template_when_missing(self):
        out = EmailService.render('welcome', {'first_name': 'Ana'}, locale='en')
        self.assertEqual(out['locale'], 'en')
        self.assertIn('Sunalyze', out['html'])


class SessionPayloadTest(_Base):
    def test_me_exposes_locale(self):
        client = self.app.test_client()
        login = client.post('/api/auth/login', json={'email': 'u@x.com', 'password': 'Secret-pass-2026'})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()['user']['locale'], 'es')
        me = client.get('/api/auth/me')
        body = me.get_json()
        self.assertEqual(body['locale'], 'es')
        self.assertEqual(body['user']['locale'], 'es')

    def test_me_anonymous_uses_accept_language(self):
        client = self.app.test_client()
        me = client.get('/api/auth/me', headers={'Accept-Language': 'en'})
        body = me.get_json()
        self.assertIsNone(body['user'])
        self.assertEqual(body['locale'], 'en')


class LocaleUpdateTest(_Base):
    def _login(self):
        client = self.app.test_client()
        r = client.post('/api/auth/login', json={'email': 'u@x.com', 'password': 'Secret-pass-2026'})
        self.assertEqual(r.status_code, 200)
        return client

    def test_patch_updates_locale(self):
        client = self._login()
        r = client.patch('/api/auth/me', json={'locale': 'en'})
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body['locale'], 'en')
        self.assertEqual(body['user']['locale'], 'en')
        db.session.expire_all()
        self.assertEqual(User.query.get(self.user.id).locale, 'en')

    def test_patch_normalizes_region_locale(self):
        client = self._login()
        r = client.patch('/api/auth/me', json={'locale': 'en-US'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['user']['locale'], 'en')

    def test_patch_rejects_unsupported_locale(self):
        client = self._login()
        r = client.patch('/api/auth/me', json={'locale': 'fr'})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.get_json()['code'], 'auth.locale_unsupported')
        db.session.expire_all()
        self.assertEqual(User.query.get(self.user.id).locale, 'es')

    def test_patch_requires_authentication(self):
        client = self.app.test_client()
        r = client.patch('/api/auth/me', json={'locale': 'en'})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()['code'], 'auth.login_required')


class NoRegressionAuthTest(_Base):
    def test_login_success_unchanged(self):
        client = self.app.test_client()
        r = client.post('/api/auth/login', json={'email': 'u@x.com', 'password': 'Secret-pass-2026'})
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body['user']['email'], 'u@x.com')
        self.assertEqual(body['role'], 'owner')

    def test_login_required_message_preserved(self):
        err = Unauthorized('Inicia sesión para continuar.', code='auth.login_required')
        self.assertEqual(err.to_dict()['error'], 'Inicia sesión para continuar.')


if __name__ == '__main__':
    unittest.main()

"""Seguridad y contrato de error del endpoint de envio de correos.

Cubre que POST /api/emails/<id>/send exige superadmin (401 anonimo, 403 logueado
sin privilegio) y que las respuestas de error llevan el campo `code` del contrato
DomainError.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
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
        self.org = Organization(nombre='Org A', type='BUSINESS', plan='pro')
        db.session.add(self.org)
        db.session.flush()
        self.user = User(email='a@example.com', first_name='Ana', last_name='Admin', email_verified=True)
        self.user.set_password('x')
        db.session.add(self.user)
        self.admin = User(email='root@example.com', first_name='Root', last_name='Super',
                          email_verified=True, is_superadmin=True)
        self.admin.set_password('x')
        db.session.add(self.admin)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=self.org.id, role='owner'))
        db.session.add(Membership(user_id=self.admin.id, org_id=self.org.id, role='owner'))
        db.session.commit()

    def _client(self, user=None):
        client = self.app.test_client()
        if user is not None:
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['org_id'] = self.org.id
        return client


class SendEmailAuthTest(_Base):
    def test_anonymous_send_is_401_with_code(self):
        client = self._client()
        resp = client.post('/api/emails/welcome/send', json={'to': 'x@example.com'})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()['code'], 'auth.login_required')

    def test_non_superadmin_send_is_403_with_code(self):
        client = self._client(self.user)
        resp = client.post('/api/emails/welcome/send', json={'to': 'x@example.com'})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()['code'], 'auth.superadmin_required')

    def test_superadmin_send_is_allowed(self):
        client = self._client(self.admin)
        resp = client.post('/api/emails/welcome/send', json={'to': 'x@example.com', 'context': {'first_name': 'Ana'}})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.get_json()['sent'])


class ErrorContractTest(_Base):
    def test_preview_unknown_template_is_404_with_code(self):
        client = self._client(self.user)
        resp = client.get('/api/emails/no-existe/preview')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()['code'], 'email.template_not_found')

    def test_send_without_to_is_422_with_code(self):
        client = self._client(self.admin)
        resp = client.post('/api/emails/welcome/send', json={})
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['code'], 'email.to_required')

    def test_panel_analysis_without_body_is_422_with_code(self):
        client = self._client(self.user)
        resp = client.post('/api/panel-analysis')
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['code'], 'request.body_required')


if __name__ == '__main__':
    unittest.main()

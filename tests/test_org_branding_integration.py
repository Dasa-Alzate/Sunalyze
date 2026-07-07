"""Tests de integración: endpoint de kinds de plantillas y branding por organización.

Base SQLite en memoria + cliente de pruebas de Flask. Cubre: `GET /api/templates/kinds`
devuelve los 8 kinds del registro; `GET/PATCH /api/org/branding` persiste, está gateado por
ORG_MANAGE (owner/admin sí, member no) y es multi-tenant (cada org ve solo su branding).
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization, OrgBrandingProfile
from app.models.membership import Membership
from app.models.flag import Flag, FlagOverride


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
        self.org_a = Organization(nombre='Org A', type='BUSINESS', plan='pro')
        self.org_b = Organization(nombre='Org B', type='BUSINESS', plan='pro')
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        self.owner_a = User(email='owner@a.com', first_name='Ana', last_name='Owner', email_verified=True)
        self.owner_a.set_password('x')
        self.member_a = User(email='member@a.com', first_name='Marta', last_name='Member', email_verified=True)
        self.member_a.set_password('x')
        self.owner_b = User(email='owner@b.com', first_name='Bob', last_name='Owner', email_verified=True)
        self.owner_b.set_password('x')
        db.session.add_all([self.owner_a, self.member_a, self.owner_b])
        db.session.flush()

        db.session.add_all([
            Membership(user_id=self.owner_a.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.member_a.id, org_id=self.org_a.id, role='member'),
            Membership(user_id=self.owner_b.id, org_id=self.org_b.id, role='owner'),
        ])
        db.session.add(Flag(key='templates', nombre='Plantillas', default_enabled=False, status='active'))
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _enable_flag(self, org):
        db.session.add(FlagOverride(flag_key='templates', scope='org', scope_id=org.id,
                                    enabled=True, source='grant'))
        db.session.commit()


class KindsEndpointTest(_Base):
    def test_kinds_returns_eight(self):
        self._enable_flag(self.org_a)
        client = self._login(self.owner_a, self.org_a)
        resp = client.get('/api/templates/kinds')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 8)
        keys = {row['key'] for row in data}
        self.assertIn('memoria_calculo', keys)
        self.assertIn('solicitud_conexion', keys)
        for row in data:
            self.assertIn('key', row)
            self.assertIn('label', row)


class BrandingEndpointTest(_Base):
    def test_get_default_branding_empty(self):
        client = self._login(self.owner_a, self.org_a)
        resp = client.get('/api/org/branding')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsNone(data['logo_path'])
        self.assertEqual(data['org_id'], self.org_a.id)

    def test_patch_persists_branding(self):
        client = self._login(self.owner_a, self.org_a)
        resp = client.patch('/api/org/branding', json={
            'logo_path': 'branding/logo.png',
            'primary_color': '#16a34a',
            'footer_text': 'Org A S.L.',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['primary_color'], '#16a34a')

        again = client.get('/api/org/branding')
        body = again.get_json()
        self.assertEqual(body['logo_path'], 'branding/logo.png')
        self.assertEqual(body['footer_text'], 'Org A S.L.')
        self.assertEqual(OrgBrandingProfile.query.filter_by(org_id=self.org_a.id).count(), 1)

    def test_member_is_forbidden(self):
        client = self._login(self.member_a, self.org_a)
        self.assertEqual(client.get('/api/org/branding').status_code, 403)
        self.assertEqual(
            client.patch('/api/org/branding', json={'primary_color': '#000000'}).status_code, 403)

    def test_admin_is_allowed(self):
        m = Membership.query.filter_by(user_id=self.member_a.id, org_id=self.org_a.id).first()
        m.role = 'admin'
        db.session.commit()
        client = self._login(self.member_a, self.org_a)
        self.assertEqual(client.get('/api/org/branding').status_code, 200)
        self.assertEqual(
            client.patch('/api/org/branding', json={'footer_text': 'X'}).status_code, 200)

    def test_branding_is_per_org(self):
        ca = self._login(self.owner_a, self.org_a)
        ca.patch('/api/org/branding', json={'footer_text': 'A footer'})
        cb = self._login(self.owner_b, self.org_b)
        cb.patch('/api/org/branding', json={'footer_text': 'B footer'})

        self.assertEqual(ca.get('/api/org/branding').get_json()['footer_text'], 'A footer')
        self.assertEqual(cb.get('/api/org/branding').get_json()['footer_text'], 'B footer')


if __name__ == '__main__':
    unittest.main()

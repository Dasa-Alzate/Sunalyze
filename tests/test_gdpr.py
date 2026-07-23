
import unittest

from app import create_app
from app.extensions import db
from app.errors import Conflict
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.services.gdpr_service import GdprService


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
        self.owner_a.set_password('secret-a')
        self.member_a = User(email='member@a.com', first_name='Marta', last_name='Member', email_verified=True)
        self.member_a.set_password('secret-m')
        self.owner_b = User(email='owner@b.com', first_name='Bob', last_name='Owner', email_verified=True)
        self.owner_b.set_password('secret-b')
        db.session.add_all([self.owner_a, self.member_a, self.owner_b])
        db.session.flush()

        db.session.add_all([
            Membership(user_id=self.owner_a.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.member_a.id, org_id=self.org_a.id, role='member'),
            Membership(user_id=self.owner_b.id, org_id=self.org_b.id, role='owner'),
        ])
        db.session.add(Project(cliente='Cliente A', org_id=self.org_a.id))
        db.session.add(Project(cliente='Cliente B', org_id=self.org_b.id))
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _make_solo(self):
        org = Organization(nombre='Personal', type='PERSONAL', plan='free')
        db.session.add(org)
        db.session.flush()
        user = User(email='solo@x.com', first_name='Solo', last_name='User', email_verified=True)
        user.set_password('solo-pass')
        db.session.add(user)
        db.session.flush()
        db.session.add(Membership(user_id=user.id, org_id=org.id, role='owner'))
        db.session.commit()
        return user, org


class ExportTest(_Base):
    def test_export_returns_user_content(self):
        client = self._login(self.member_a, self.org_a)
        resp = client.get('/api/gdpr/export')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['user']['email'], 'member@a.com')
        self.assertEqual(body['export_metadata']['gdpr_articles'], ['15', '20'])
        org_ids = {m['org_id'] for m in body['memberships']}
        self.assertEqual(org_ids, {self.org_a.id})

    def test_export_excludes_secrets(self):
        client = self._login(self.member_a, self.org_a)
        body = client.get('/api/gdpr/export').get_json()
        self.assertNotIn('password_hash', body['user'])
        self.assertNotIn('mfa_secret', body['user'])
        self.assertNotIn('mfa_recovery_codes', body['user'])

    def test_export_is_tenant_isolated(self):
        client = self._login(self.owner_a, self.org_a)
        body = client.get('/api/gdpr/export').get_json()
        owned_ids = {o['organization']['id'] for o in body['owned_organizations']}
        self.assertEqual(owned_ids, {self.org_a.id})
        clientes = {p['cliente'] for o in body['owned_organizations'] for p in o['projects']}
        self.assertIn('Cliente A', clientes)
        self.assertNotIn('Cliente B', clientes)

    def test_member_owns_no_organizations(self):
        client = self._login(self.member_a, self.org_a)
        body = client.get('/api/gdpr/export').get_json()
        self.assertEqual(body['owned_organizations'], [])


class EraseTest(_Base):
    def test_erase_anonymizes_in_place(self):
        user, _ = self._make_solo()
        uid = user.id
        client = self._login(user, user.memberships[0].organization)
        resp = client.delete('/api/gdpr/account')
        self.assertEqual(resp.status_code, 200)

        row = User.query.get(uid)
        self.assertIsNotNone(row)
        self.assertTrue(row.is_deleted)
        self.assertTrue(row.email.endswith('@anonymized.invalid'))
        self.assertEqual(row.first_name, 'Usuario')
        self.assertEqual(row.last_name, 'anonimizado')
        self.assertFalse(row.email_verified)
        self.assertFalse(row.check_password('solo-pass'))

    def test_erase_soft_deletes_personal_org_and_memberships(self):
        user, org = self._make_solo()
        oid = org.id
        GdprService.erase_account(user)
        self.assertTrue(Organization.query.get(oid).is_deleted)
        self.assertEqual(Membership.query.filter_by(user_id=user.id).count(), 0)

    def test_erase_conflicts_for_sole_owner_of_shared_org(self):
        client = self._login(self.owner_a, self.org_a)
        resp = client.delete('/api/gdpr/account')
        self.assertEqual(resp.status_code, 409)
        self.assertIsNotNone(User.query.get(self.owner_a.id))
        self.assertFalse(User.query.get(self.owner_a.id).is_deleted)

    def test_erase_is_not_repeatable(self):
        user, _ = self._make_solo()
        GdprService.erase_account(user)
        with self.assertRaises(Conflict):
            GdprService.erase_account(user)


class GdprGatesTest(_Base):
    def test_export_requires_session(self):
        self.assertEqual(self.app.test_client().get('/api/gdpr/export').status_code, 401)

    def test_delete_requires_session(self):
        self.assertEqual(self.app.test_client().delete('/api/gdpr/account').status_code, 401)

    def test_forbidden_without_workspace_role(self):
        client = self._login(self.member_a, self.org_b)
        self.assertEqual(client.get('/api/gdpr/export').status_code, 403)
        self.assertEqual(client.delete('/api/gdpr/account').status_code, 403)


if __name__ == '__main__':
    unittest.main()

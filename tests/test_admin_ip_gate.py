
import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership


def _make_app(allowlist=''):
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite://',
        WTF_CSRF_ENABLED=False,
        SUPERADMIN_IP_ALLOWLIST=allowlist,
        SUPERADMIN_TRUST_PROXY=False,
    )
    return app


class AdminIpGateTest(unittest.TestCase):
    def _setup_app(self, allowlist):
        self.app = _make_app(allowlist)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = Organization(nombre='Org A', type='BUSINESS', plan='pro')
        db.session.add(self.org)
        db.session.flush()
        self.superadmin = User(email='su@a.com', first_name='Su', last_name='Per',
                               email_verified=True, is_superadmin=True)
        self.superadmin.set_password('x')
        db.session.add(self.superadmin)
        db.session.flush()
        db.session.add(Membership(user_id=self.superadmin.id, org_id=self.org.id, role='owner'))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _client(self, remote_addr):
        client = self.app.test_client()
        client.environ_base['REMOTE_ADDR'] = remote_addr
        with client.session_transaction() as sess:
            sess['user_id'] = self.superadmin.id
            sess['org_id'] = self.org.id
        return client

    def test_unlisted_ip_gets_403_json_with_code(self):
        self._setup_app('10.0.0.1, 192.168.1.0/24')
        client = self._client('203.0.113.7')
        for path in ('/api/admin/flags', '/api/admin/organizations', '/api/admin/users'):
            with self.subTest(path=path):
                resp = client.get(path)
                self.assertEqual(resp.status_code, 403)
                self.assertEqual(resp.content_type, 'application/json')
                self.assertEqual(resp.get_json().get('code'), 'admin.ip_not_allowed')

    def test_unlisted_ip_blocked_before_auth(self):
        self._setup_app('10.0.0.1')
        client = self.app.test_client()
        client.environ_base['REMOTE_ADDR'] = '203.0.113.7'
        resp = client.get('/api/admin/flags')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get('code'), 'admin.ip_not_allowed')

    def test_listed_ip_passes(self):
        self._setup_app('10.0.0.1, 192.168.1.0/24')
        client = self._client('192.168.1.42')
        resp = client.get('/api/admin/flags')
        self.assertEqual(resp.status_code, 200)

    def test_empty_allowlist_means_no_filter(self):
        self._setup_app('')
        client = self._client('203.0.113.7')
        resp = client.get('/api/admin/users')
        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()

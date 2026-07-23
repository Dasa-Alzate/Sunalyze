
import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.audit_event import AuditEvent


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class WorkspaceSwitchTest(unittest.TestCase):
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
        self.org_a = Organization(nombre='Org A', type='BUSINESS', plan='pro', seats=5)
        self.org_b = Organization(nombre='Org B', type='BUSINESS', plan='pro', seats=5)
        self.org_c = Organization(nombre='Org C', type='BUSINESS', plan='pro', seats=5)
        db.session.add_all([self.org_a, self.org_b, self.org_c])
        db.session.flush()
        self.multi = User(email='multi@a.com', first_name='Mul', last_name='Ti', email_verified=True)
        self.multi.set_password('x')
        self.mono = User(email='mono@a.com', first_name='Mo', last_name='No', email_verified=True)
        self.mono.set_password('x')
        db.session.add_all([self.multi, self.mono])
        db.session.flush()
        db.session.add_all([
            Membership(user_id=self.multi.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.multi.id, org_id=self.org_b.id, role='member'),
            Membership(user_id=self.mono.id, org_id=self.org_c.id, role='owner'),
            Project(org_id=self.org_a.id, cliente='Cliente A'),
            Project(org_id=self.org_b.id, cliente='Cliente B'),
        ])
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def test_list_marks_active_workspace(self):
        client = self._login(self.multi, self.org_a)
        data = client.get('/api/workspace').get_json()
        self.assertEqual(len(data['workspaces']), 2)
        active = [w for w in data['workspaces'] if w['active']]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['org_id'], self.org_a.id)
        self.assertEqual(active[0]['role'], 'owner')

    def test_mono_org_user_lists_one(self):
        client = self._login(self.mono, self.org_c)
        data = client.get('/api/workspace').get_json()
        self.assertEqual(len(data['workspaces']), 1)
        self.assertTrue(data['workspaces'][0]['active'])

    def test_valid_switch_rescopes_projects(self):
        client = self._login(self.multi, self.org_a)
        before = client.get('/api/projects').get_json()
        self.assertEqual([p['cliente'] for p in before], ['Cliente A'])

        resp = client.post('/api/workspace/switch', json={'org_id': self.org_b.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['org_id'], self.org_b.id)

        after = client.get('/api/projects').get_json()
        self.assertEqual([p['cliente'] for p in after], ['Cliente B'])

        events = AuditEvent.query.filter_by(action='workspace.switch').all()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].org_id, self.org_b.id)
        self.assertEqual(events[0].actor_user_id, self.multi.id)

    def test_switch_to_foreign_org_is_404(self):
        client = self._login(self.multi, self.org_a)
        resp = client.post('/api/workspace/switch', json={'org_id': self.org_c.id})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json().get('code'), 'workspace.not_found')
        self.assertEqual(
            [p['cliente'] for p in client.get('/api/projects').get_json()],
            ['Cliente A'],
        )

    def test_switch_to_missing_org_is_404(self):
        client = self._login(self.multi, self.org_a)
        resp = client.post('/api/workspace/switch', json={'org_id': 9999})
        self.assertEqual(resp.status_code, 404)

    def test_switch_requires_login(self):
        client = self.app.test_client()
        self.assertEqual(client.get('/api/workspace').status_code, 401)
        self.assertEqual(
            client.post('/api/workspace/switch', json={'org_id': self.org_a.id}).status_code, 401)


if __name__ == '__main__':
    unittest.main()

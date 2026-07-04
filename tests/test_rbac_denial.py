"""Suite parametrizada de denegacion RBAC.

Verifica de forma compacta que un usuario cuyo rol NO concede el permiso exigido
por `@require_permission` recibe 403 (codigo `authz.forbidden`) en un endpoint
representativo de cada blueprint protegido, y que un no-superadmin recibe 403 en
`/api/admin/*`. El rol usado es `member`, que segun `ROLE_PERMISSIONS` carece de
todos los permisos de administracion probados aqui.
"""

import unittest

from app import create_app
from app.extensions import db
from app.authz import ROLE_PERMISSIONS, Permission
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.flag import Flag, FlagOverride


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


DENIED_CASES = [
    ('member:invite', 'POST', '/api/invitations', Permission.MEMBER_INVITE),
    ('members', 'PATCH', '/api/members/999', Permission.MEMBER_MANAGE),
    ('catalogs', 'POST', '/api/catalogs', Permission.CATALOG_MANAGE),
    ('legalization', 'POST', '/api/projects/999/legalization/transition', Permission.PROJECT_LEGALIZE),
    ('audit', 'GET', '/api/audit', Permission.AUDIT_VIEW),
    ('templates', 'POST', '/api/templates', Permission.TEMPLATE_MANAGE),
    ('org', 'PATCH', '/api/org/branding', Permission.ORG_MANAGE),
    ('project:delete', 'DELETE', '/api/projects/999', Permission.PROJECT_DELETE),
]


class RbacDenialTest(unittest.TestCase):
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
        self.member = User(email='member@a.com', first_name='Marta', last_name='Member', email_verified=True)
        self.member.set_password('x')
        self.superadmin = User(email='su@a.com', first_name='Su', last_name='Per',
                               email_verified=True, is_superadmin=True)
        self.superadmin.set_password('x')
        db.session.add_all([self.member, self.superadmin])
        db.session.flush()
        db.session.add_all([
            Membership(user_id=self.member.id, org_id=self.org.id, role='member'),
            Membership(user_id=self.superadmin.id, org_id=self.org.id, role='member'),
        ])
        db.session.add(Flag(key='templates', nombre='Plantillas', default_enabled=False, status='active'))
        db.session.add(FlagOverride(flag_key='templates', scope='org', scope_id=self.org.id,
                                    enabled=True, source='grant'))
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _request(self, client, method, path):
        return client.open(path, method=method, json={})

    def test_member_role_lacks_probed_permissions(self):
        granted = ROLE_PERMISSIONS['member']
        for _, _, _, permission in DENIED_CASES:
            with self.subTest(permission=permission):
                self.assertNotIn(permission, granted)

    def test_insufficient_role_is_forbidden(self):
        client = self._login(self.member, self.org)
        for name, method, path, _ in DENIED_CASES:
            with self.subTest(endpoint=name):
                resp = self._request(client, method, path)
                self.assertEqual(resp.status_code, 403, f'{name}: se esperaba 403')
                self.assertEqual(resp.get_json().get('code'), 'authz.forbidden',
                                 f'{name}: 403 por motivo distinto al RBAC')

    def test_unauthenticated_is_unauthorized(self):
        """Sin sesion -> 401. Se excluye `templates`, gateado por `@require_flag`
        (que precede a la autenticacion), por lo que responde 403 feature_disabled."""
        client = self.app.test_client()
        for name, method, path, _ in DENIED_CASES:
            if name == 'templates':
                continue
            with self.subTest(endpoint=name):
                resp = self._request(client, method, path)
                self.assertEqual(resp.status_code, 401, f'{name}: se esperaba 401 sin sesion')

    def test_non_superadmin_forbidden_on_admin_api(self):
        client = self._login(self.member, self.org)
        for path in ('/api/admin/users', '/api/admin/organizations', '/api/admin/flags'):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 403)

    def test_superadmin_allowed_on_admin_api(self):
        client = self._login(self.superadmin, self.org)
        self.assertEqual(client.get('/api/admin/users').status_code, 200)


if __name__ == '__main__':
    unittest.main()

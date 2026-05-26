"""Tests de la convencion REST uniforme y del generador `flask api-map`.

Cubre: update por PATCH de panel y de proyecto (200 + persiste), retirada del verbo PUT
(405) en esos recursos, y que `flask api-map` escribe docs/api-map.md con los endpoints /api.
"""

import os
import unittest

from app import create_app
from app.extensions import db
from app.cli import _api_rows, _render_api_map
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.panel import Panel
from app.services.catalog_service import CatalogService


def _make_app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite://',
        WTF_CSRF_ENABLED=False,
    )
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
        self.user = User(email='a@example.com', first_name='Ana', last_name='Admin',
                         email_verified=True)
        self.user.set_password('x')
        db.session.add(self.user)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=self.org.id, role='owner'))
        db.session.commit()
        self.catalog = CatalogService.ensure_default_catalog(self.org.id)
        db.session.commit()

    def _login(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = self.org.id
        return client


class PatchUpdateTest(_Base):
    def test_patch_panel_persists_and_put_is_405(self):
        client = self._login()
        resp = client.post('/api/panels', json={
            'nombre': 'LR5-410', 'power': 410.0, 'voc': 37.2, 'vmp': 31.0,
            'imp': 13.2, 'catalog_id': self.catalog.id,
        })
        self.assertEqual(resp.status_code, 201)
        panel_id = resp.get_json()['id']

        resp = client.patch(f'/api/panels/{panel_id}', json={'power': 420.0})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['power'], 420.0)
        self.assertEqual(Panel.query.get(panel_id).power, 420.0)

        resp = client.put(f'/api/panels/{panel_id}', json={'power': 999.0})
        self.assertEqual(resp.status_code, 405)

    def test_patch_project_persists_and_put_is_405(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'Cliente A'})
        self.assertEqual(resp.status_code, 201)
        project_id = resp.get_json()['id']

        resp = client.patch(f'/api/projects/{project_id}', json={'direccion': 'Calle 1'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['direccion'], 'Calle 1')
        self.assertEqual(Project.query.get(project_id).direccion, 'Calle 1')

        resp = client.put(f'/api/projects/{project_id}', json={'direccion': 'Calle 2'})
        self.assertEqual(resp.status_code, 405)


class ApiMapTest(_Base):
    def test_api_map_rows_are_all_api(self):
        rows = _api_rows()
        self.assertTrue(rows)
        self.assertTrue(all(r['rule'].startswith('/api') for r in rows))

    def test_render_is_idempotent(self):
        rows = _api_rows()
        self.assertEqual(_render_api_map(rows), _render_api_map(rows))

    def test_command_writes_file(self):
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=['api-map'])
        self.assertEqual(result.exit_code, 0, result.output)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_path = os.path.join(root, 'docs', 'api-map.md')
        self.assertTrue(os.path.isfile(out_path))
        with open(out_path, encoding='utf-8') as fh:
            content = fh.read()
        self.assertIn('# API map', content)
        self.assertIn('/api/projects', content)
        self.assertIn('PATCH', content)


if __name__ == '__main__':
    unittest.main()

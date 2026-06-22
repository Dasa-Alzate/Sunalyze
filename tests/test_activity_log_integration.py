"""Tests de integracion de la bitacora de actividad (backlog §1).

Usa SQLite en memoria y el cliente de pruebas de Flask. Cubre: soft-delete y
restore de proyecto y catalogo, unicidad de nombre de catalogo ignorando
borrados, feed paginado de /api/audit con enlace resuelto, cobertura de audit
en acciones de equipo y catalogo, y no-regresion del CRUD existente.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.catalog import Catalog
from app.models.panel import Panel
from app.models.audit_event import AuditEvent
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


class ProjectSoftDeleteTest(_Base):
    def _create_project(self, client, cliente='Cliente X'):
        resp = client.post('/api/projects', json={'cliente': cliente})
        self.assertEqual(resp.status_code, 201)
        return resp.get_json()['id']

    def test_delete_is_soft_and_hidden_from_listing(self):
        client = self._login()
        pid = self._create_project(client)

        resp = client.delete(f'/api/projects/{pid}')
        self.assertEqual(resp.status_code, 200)

        row = Project.query.get(pid)
        self.assertIsNotNone(row)
        self.assertTrue(row.is_deleted)
        self.assertEqual(Project.with_deleted().count(), 1)
        self.assertEqual(Project.active().count(), 0)

        listing = client.get('/api/projects').get_json()
        self.assertEqual(listing, [])

        self.assertEqual(client.get(f'/api/projects/{pid}').status_code, 404)

    def test_restore_reactivates(self):
        client = self._login()
        pid = self._create_project(client)
        client.delete(f'/api/projects/{pid}')

        resp = client.post(f'/api/projects/{pid}/restore')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Project.query.get(pid).is_deleted)

        listing = client.get('/api/projects').get_json()
        self.assertEqual(len(listing), 1)

    def test_restore_other_org_is_404(self):
        client = self._login()
        pid = self._create_project(client)
        client.delete(f'/api/projects/{pid}')

        other_org = Organization(nombre='Org B', type='BUSINESS', plan='pro')
        db.session.add(other_org)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=other_org.id, role='owner'))
        db.session.commit()

        intruder = self.app.test_client()
        with intruder.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = other_org.id
        self.assertEqual(intruder.post(f'/api/projects/{pid}/restore').status_code, 404)


class CatalogSoftDeleteTest(_Base):
    def test_delete_is_soft_and_restore(self):
        client = self._login()
        resp = client.post('/api/catalogs', json={'nombre': 'Catalogo 1'})
        self.assertEqual(resp.status_code, 201)
        cid = resp.get_json()['id']

        self.assertEqual(client.delete(f'/api/catalogs/{cid}').status_code, 200)
        row = Catalog.query.get(cid)
        self.assertTrue(row.is_deleted)

        library = client.get('/api/catalogs').get_json()
        self.assertNotIn(cid, [c['id'] for c in library])

        self.assertEqual(client.post(f'/api/catalogs/{cid}/restore').status_code, 200)
        self.assertFalse(Catalog.query.get(cid).is_deleted)
        library = client.get('/api/catalogs').get_json()
        self.assertIn(cid, [c['id'] for c in library])

    def test_name_uniqueness_ignores_deleted(self):
        client = self._login()
        resp = client.post('/api/catalogs', json={'nombre': 'Repetible'})
        cid = resp.get_json()['id']
        client.delete(f'/api/catalogs/{cid}')

        resp2 = client.post('/api/catalogs', json={'nombre': 'Repetible'})
        self.assertEqual(resp2.status_code, 201)
        self.assertNotEqual(resp2.get_json()['id'], cid)

    def test_ensure_default_catalog_after_soft_delete_creates_new(self):
        self.catalog.soft_delete()
        db.session.commit()
        fresh = CatalogService.ensure_default_catalog(self.org.id)
        db.session.commit()
        self.assertNotEqual(fresh.id, self.catalog.id)
        self.assertFalse(fresh.is_deleted)


class AuditFeedTest(_Base):
    def test_feed_paginates_and_resolves_link(self):
        client = self._login()
        for i in range(3):
            client.post('/api/projects', json={'cliente': f'C{i}'})

        page = client.get('/api/audit?limit=2&offset=0').get_json()
        self.assertEqual(page['limit'], 2)
        self.assertEqual(page['offset'], 0)
        self.assertEqual(page['total'], 3)
        self.assertTrue(page['has_more'])
        self.assertEqual(len(page['items']), 2)

        first = page['items'][0]
        self.assertEqual(first['action'], 'project.create')
        self.assertTrue(first['link'].startswith('/app/proyectos/'))

        page2 = client.get('/api/audit?limit=2&offset=2').get_json()
        self.assertEqual(len(page2['items']), 1)
        self.assertFalse(page2['has_more'])

    def test_equipment_action_generates_audit(self):
        client = self._login()
        resp = client.post('/api/panels', json={
            'nombre': 'Panel X', 'power': 450, 'voc': 49, 'vmp': 41, 'imp': 11,
            'catalog_id': self.catalog.id,
        })
        self.assertEqual(resp.status_code, 201)
        ev = AuditEvent.query.filter_by(action='equipment.create').first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.entity_type, 'panels')
        self.assertEqual(ev.org_id, self.org.id)

    def test_catalog_action_generates_audit(self):
        client = self._login()
        client.post('/api/catalogs', json={'nombre': 'Cat audit'})
        self.assertIsNotNone(AuditEvent.query.filter_by(action='catalog.create').first())


class NoRegressionTest(_Base):
    def test_existing_project_crud_still_works(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'No regresion'})
        self.assertEqual(resp.status_code, 201)
        pid = resp.get_json()['id']

        resp = client.patch(f'/api/projects/{pid}', json={'localidad': 'Madrid'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['localidad'], 'Madrid')

        self.assertEqual(client.get(f'/api/projects/{pid}').status_code, 200)

    def test_equipment_crud_delete_still_physical(self):
        client = self._login()
        resp = client.post('/api/panels', json={
            'nombre': 'Panel Y', 'power': 400, 'voc': 48, 'vmp': 40, 'imp': 10,
            'catalog_id': self.catalog.id,
        })
        item_id = resp.get_json()['id']
        self.assertEqual(client.delete(f'/api/panels/{item_id}').status_code, 200)
        self.assertEqual(Panel.query.count(), 0)


if __name__ == '__main__':
    unittest.main()

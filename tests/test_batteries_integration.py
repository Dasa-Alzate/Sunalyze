"""Tests de integración de baterías (Fase 1, backend core).

Usa SQLite en memoria y el cliente de pruebas de Flask. Cubre: CRUD de batería en
catálogo vía API, asignación de batería a proyecto (battery_id + battery_quantity
aparecen en to_dict), criterios del scraper (VITAL['battery'] y acceptance.evaluate
accepted/blocked/review) y no-regresión del CRUD de paneles/inversores.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.battery import Battery
from app.services.catalog_service import CatalogService
from app.scrapers.base import VITAL, NormalizedProduct
from app.scrapers.acceptance import evaluate


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


class BatteryCrudTest(_Base):
    def test_create_read_update_delete_battery(self):
        client = self._login()

        resp = client.post('/api/batteries', json={
            'nombre': 'Test LiFePO4 10kWh',
            'capacity_kwh': 10.24,
            'power_kw': 5.0,
            'voltage': 51.2,
            'technology': 'LiFePO4',
            'round_trip_efficiency': 95.0,
            'max_cycles': 6000,
            'catalog_id': self.catalog.id,
        })
        self.assertEqual(resp.status_code, 201)
        created = resp.get_json()
        bat_id = created['id']
        self.assertEqual(created['capacity_kwh'], 10.24)
        self.assertEqual(created['technology'], 'LiFePO4')
        self.assertEqual(created['source'], 'manual')
        self.assertTrue(created['editable'])

        resp = client.get(f'/api/batteries/{bat_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['nombre'], 'Test LiFePO4 10kWh')

        resp = client.get('/api/batteries')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()), 1)

        resp = client.put(f'/api/batteries/{bat_id}', json={'power_kw': 6.5})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['power_kw'], 6.5)

        resp = client.delete(f'/api/batteries/{bat_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Battery.query.count(), 0)

    def test_create_battery_missing_vital_is_400(self):
        client = self._login()
        resp = client.post('/api/batteries', json={'nombre': 'Incompleta'})
        self.assertEqual(resp.status_code, 422)


class BatteryProjectTest(_Base):
    def test_assign_battery_to_project_appears_in_to_dict(self):
        battery = Battery(nombre='BYD HVS 5.1', capacity_kwh=5.12, power_kw=5.1,
                          voltage=204.0, catalog_id=self.catalog.id)
        db.session.add(battery)
        db.session.flush()

        project = Project(cliente='Cliente A', org_id=self.org.id,
                          battery_id=battery.id, battery_quantity=3)
        db.session.add(project)
        db.session.commit()

        data = project.to_dict()
        self.assertEqual(data['battery_id'], battery.id)
        self.assertEqual(data['battery_quantity'], 3)
        self.assertEqual(data['battery_nombre'], 'BYD HVS 5.1')


class BatteryScraperTest(_Base):
    def test_vital_battery_defined(self):
        self.assertEqual(VITAL['battery'], ('nombre', 'capacity_kwh', 'power_kw', 'voltage'))

    def _product(self, **fields):
        return NormalizedProduct(kind='battery', external_id='ext-1',
                                 source_url='http://x', fields=fields)

    def test_accepted_battery(self):
        product = self._product(nombre='BYD HVS 5.1', capacity_kwh=5.12,
                                 power_kw=5.1, voltage=204.0,
                                 round_trip_efficiency=96.0, dod=100.0)
        self.assertTrue(product.is_valid)
        self.assertEqual(evaluate(product, 'BYD')['verdict'], 'accepted')

    def test_blocked_battery_out_of_range(self):
        product = self._product(nombre='Falsa', capacity_kwh=0.1,
                                 power_kw=5.0, voltage=51.2)
        result = evaluate(product, 'BYD')
        self.assertEqual(result['verdict'], 'blocked')
        self.assertTrue(result['block'])

    def test_review_battery(self):
        product = self._product(nombre='Industrial', capacity_kwh=120.0,
                                 power_kw=50.0, voltage=51.2)
        result = evaluate(product, 'BYD')
        self.assertEqual(result['verdict'], 'review')
        self.assertFalse(result['block'])
        self.assertTrue(result['review'])


class NoRegressionTest(_Base):
    def test_panel_crud_still_works(self):
        client = self._login()
        resp = client.post('/api/panels', json={
            'nombre': 'LR5-410', 'power': 410.0, 'voc': 37.2, 'vmp': 31.0,
            'imp': 13.2, 'catalog_id': self.catalog.id,
        })
        self.assertEqual(resp.status_code, 201)
        resp = client.get('/api/panels')
        self.assertEqual(len(resp.get_json()), 1)

    def test_inverter_crud_still_works(self):
        client = self._login()
        resp = client.post('/api/inverters', json={
            'nombre': 'SUN2000-5KTL', 'power': 5.0, 'vmax': 600.0,
            'I_max_input': 11.0, 'I_max_output': 7.5, 'catalog_id': self.catalog.id,
        })
        self.assertEqual(resp.status_code, 201)
        resp = client.get('/api/inverters')
        self.assertEqual(len(resp.get_json()), 1)


if __name__ == '__main__':
    unittest.main()


import unittest
from unittest.mock import patch

import pandas as pd

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.services.catalog_service import CatalogService
from app.services.analysis_service import AnalysisService
from app.services.template_engine.catalog import variable_catalog, whitelist
from app.services.template_engine import render_version
from app.services.circuit import CircuitService, DCConfig, ACConfig, SystemConfig
from app.scrapers.base import VITAL, NormalizedProduct
from app.scrapers.acceptance import evaluate


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
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

        resp = client.patch(f'/api/batteries/{bat_id}', json={'power_kw': 6.5})
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


def _fake_pvgis_df():
    idx = pd.date_range('2020-01-01', periods=24 * 30, freq='h')
    n = len(idx)
    df = pd.DataFrame(
        {
            'poa_direct': [400.0] * n,
            'poa_sky_diffuse': [100.0] * n,
            'poa_ground_diffuse': [20.0] * n,
            'temp_air': [20.0] * n,
        },
        index=idx,
    )
    meta = {'inputs': {'location': {'elevation': 100.0}}}
    return df, meta


class BatteryPatchPersistTest(_Base):
    def _make_battery(self):
        battery = Battery(nombre='Pylontech US5000', capacity_kwh=4.8, power_kw=3.5,
                          voltage=48.0, usable_kwh=4.56, dod=95.0,
                          round_trip_efficiency=96.0, technology='LiFePO4',
                          max_cycles=6000, catalog_id=self.catalog.id)
        db.session.add(battery)
        db.session.flush()
        return battery

    def test_patch_assigns_battery_and_persists(self):
        client = self._login()
        battery = self._make_battery()
        db.session.commit()

        resp = client.post('/api/projects', json={'cliente': 'Cliente Bat'})
        self.assertEqual(resp.status_code, 201)
        project_id = resp.get_json()['id']

        resp = client.patch(f'/api/projects/{project_id}', json={
            'battery_id': battery.id, 'battery_quantity': 2,
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['battery_id'], battery.id)
        self.assertEqual(body['battery_quantity'], 2)
        self.assertEqual(body['battery_nombre'], 'Pylontech US5000')

        reloaded = Project.query.get(project_id)
        self.assertEqual(reloaded.battery_id, battery.id)
        self.assertEqual(reloaded.battery_quantity, 2)

    def test_patch_invalid_battery_is_404(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'X'})
        project_id = resp.get_json()['id']
        resp = client.patch(f'/api/projects/{project_id}', json={'battery_id': 99999})
        self.assertEqual(resp.status_code, 404)


class BatteryAnalysisTest(_Base):
    def test_battery_analysis_heuristic_contract(self):
        battery = Battery(nombre='Bank', capacity_kwh=10.0, power_kw=5.0, voltage=48.0,
                          usable_kwh=9.0, dod=90.0, round_trip_efficiency=95.0,
                          catalog_id=self.catalog.id)
        out = AnalysisService._battery_analysis(
            battery, quantity=2, necesidad=8_000_000, autoconsumo=0.4,
            annual_production=12000,
        )
        self.assertEqual(out['bank_usable_kwh'], 18.0)
        self.assertEqual(out['method'], 'daily_balance_v1')
        self.assertGreater(out['estimated_self_consumption_pct'], 40.0)
        self.assertLessEqual(out['estimated_self_consumption_pct'], 100.0)
        self.assertGreaterEqual(out['recommended_capacity_kwh'], 0.0)
        self.assertIn('horaria', out['method_note'])

    def _seed_equipment(self):
        panel = Panel(nombre='LR5-410', power=410.0, voc=37.2, vmp=31.0, imp=13.2,
                      isc=14.0, y=21.0, width=1722, height=1134, tcp=0.34, tcv=0.25,
                      t_noct=45.0, catalog_id=self.catalog.id)
        battery = Battery(nombre='HVS', capacity_kwh=5.12, power_kw=5.1, voltage=204.0,
                          usable_kwh=5.0, dod=95.0, round_trip_efficiency=96.0,
                          catalog_id=self.catalog.id)
        db.session.add_all([panel, battery])
        db.session.flush()
        return panel, battery

    def test_calculate_with_and_without_battery(self):
        panel, battery = self._seed_equipment()
        db.session.commit()
        base = {
            'panel_id': panel.id, 'latitud': 40.0, 'longitud': -3.0,
            'autoconsumo': 40, 'necesidad': 5000000,
        }
        with patch('app.services.analysis_service.PvgisClient.get_hourly',
                   return_value=_fake_pvgis_df()):
            without = AnalysisService.calculate(dict(base), visible_catalog_ids=[self.catalog.id])
            self.assertNotIn('battery', without)

            with_bat = AnalysisService.calculate(
                {**base, 'battery_id': battery.id, 'battery_quantity': 2},
                visible_catalog_ids=[self.catalog.id],
            )
            self.assertIn('battery', with_bat)
            self.assertEqual(with_bat['battery']['battery_id'], battery.id)
            self.assertEqual(with_bat['battery']['quantity'], 2)
            self.assertEqual(with_bat['total_field_power'], without['total_field_power'])


class BatteryCatalogVarsTest(_Base):
    def test_battery_entity_in_catalog_and_whitelist(self):
        groups = variable_catalog('memoria_calculo')
        entities = {g['entity'] for g in groups}
        self.assertIn('battery', entities)
        battery_group = next(g for g in groups if g['entity'] == 'battery')
        paths = {v['path'] for v in battery_group['vars']}
        for attr in ('nombre', 'capacity_kwh', 'usable_kwh', 'dod', 'power_kw',
                     'voltage', 'technology', 'round_trip_efficiency', 'max_cycles'):
            self.assertIn(f'battery.{attr}', paths)
        self.assertIn('capacity_kwh', whitelist()['battery'])

    def test_render_version_resolves_battery_var(self):
        battery = Battery(nombre='HVS', capacity_kwh=5.12, power_kw=5.1, voltage=204.0,
                          catalog_id=self.catalog.id)
        db.session.add(battery)
        db.session.flush()
        project = Project(cliente='C', org_id=self.org.id, battery_id=battery.id)
        db.session.add(project)
        db.session.commit()

        version = [{'id': 1, 'type': 'text', 'title': 'Bateria',
                    'body': 'Capacidad: {{ battery.capacity_kwh }} kWh'}]
        out = render_version(version, project)
        self.assertIn('5.12', out['html'])

    def test_render_version_battery_absent_no_break(self):
        project = Project(cliente='SinBat', org_id=self.org.id)
        db.session.add(project)
        db.session.commit()
        version = [{'id': 1, 'type': 'text', 'title': 'B',
                    'body': 'Modelo: {{ battery.nombre }}'}]
        out = render_version(version, project)
        self.assertIsInstance(out['html'], str)


class BatteryDiagramTest(unittest.TestCase):
    def _config(self, has_battery):
        dc = DCConfig(panel_model='LR5', panel_voc=37.2, panel_isc=14.0,
                      panels_per_string=10, num_strings=2, fuse_i=17.5,
                      switch_v=600.0, cable_section='6 mm²')
        ac = ACConfig(inverter_model='SUN2000', inverter_power=5.0, inverter_output_i=7.5,
                      phases=1, mcb_i=10.0, rcd_i=25.0, rcd_sensitivity='30 mA',
                      cable_section='6 mm²', has_battery=has_battery,
                      battery_model='HVS 5.1' if has_battery else '')
        return SystemConfig(dc=dc, ac=ac)

    def test_full_system_includes_battery_when_present(self):
        svg_with = CircuitService.generate_full_system(self._config(True))
        svg_without = CircuitService.generate_full_system(self._config(False))
        self.assertIn('<svg', svg_with)
        self.assertIn('HVS 5.1', svg_with)
        self.assertNotIn('HVS 5.1', svg_without)
        self.assertNotIn('Bateria', svg_without)


if __name__ == '__main__':
    unittest.main()

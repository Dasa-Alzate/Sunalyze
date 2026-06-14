"""Tests del banco oficial de tipos de documento (España).

Verifica que `DocumentBankSeeder.seed()` crea N plantillas system con los tags correctos
(country/required_by/stage/kind), es idempotente (correr dos veces no duplica), que cada
plantilla renderiza contra un proyecto de ejemplo (con instalación, mantenimiento e
incidencia para las de posventa) sin error y con variables resueltas, y que aparecen en el
banco system vía `GET /api/templates/bank`.
"""

import unittest
from datetime import date

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.installation import Installation, MaintenanceVisit, Incident
from app.models.financial_scenario import FinancialScenario
from app.models.flag import Flag, FlagOverride
from app.models.report_template import ReportTemplate, TemplateVersion
from app.services.document_bank import DocumentBankSeeder, OFFICIAL_TEMPLATES_ES
from app.services.template_engine import render_version


def _make_app():
    return create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
    })


class _Base(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed_fixtures()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_fixtures(self):
        self.org = Organization(nombre='Org A', type='BUSINESS', plan='pro')
        db.session.add(self.org)
        db.session.flush()

        self.user = User(email='a@example.com', first_name='Ana', last_name='Admin',
                         email_verified=True)
        self.user.set_password('x')
        db.session.add(self.user)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=self.org.id, role='owner'))

        self.panel = Panel(nombre='LR5-410', voc=37.2, vmp=31.0, imp=13.2, isc=14.0,
                           power=410.0, height=1722, width=1134)
        self.inverter = Inverter(nombre='SUN2000', power=5.0, vmax=600.0)
        self.battery = Battery(nombre='HVS 5.1', capacity_kwh=5.12, usable_kwh=5.12,
                               power_kw=5.1, voltage=204.0, technology='LiFePO4')
        db.session.add_all([self.panel, self.inverter, self.battery])
        db.session.flush()

        self.project = Project(
            cliente='Cliente A', org_id=self.org.id,
            panel_id=self.panel.id, inverter_id=self.inverter.id, battery_id=self.battery.id,
            direccion='Calle Sol 1', localidad='Sevilla', cups='ES0021000000000000XY',
            compania='Endesa', potencia_contratada=5.75, tipo_voltaje='monofasico',
            referencia_catastral='1234567AB1234C', inclinacion=30.0, azimut=0.0,
            latitud=37.3886, longitud=-5.9823,
        )
        self.project.resultados = {'total_field_power': 4.1, 'cell_amount': 10}
        db.session.add(self.project)
        db.session.flush()

        self.installation = Installation(
            org_id=self.org.id, project_id=self.project.id, status='operativa',
            commissioned_at=date(2025, 1, 15), warranty_until=date(2035, 1, 15),
            expected_annual_kwh=7200.0, notes='Sin observaciones.',
        )
        db.session.add(self.installation)
        db.session.flush()
        db.session.add(MaintenanceVisit(
            org_id=self.org.id, installation_id=self.installation.id, kind='preventivo',
            status='realizada', scheduled_at=date(2025, 6, 1), done_at=date(2025, 6, 2),
            technician='Pepe', notes='Limpieza de módulos.'))
        db.session.add(Incident(
            org_id=self.org.id, installation_id=self.installation.id, title='String 2 sin producción',
            description='Caída de un string.', severity='alta', status='abierta',
            opened_at=date(2025, 6, 3)))

        scenario = FinancialScenario(
            org_id=self.org.id, project_id=self.project.id, name='Base', is_default=True)
        scenario.results = {
            'capex': {'net_eur': 8500.0},
            'annual_saving_year1_eur': 1200.0,
            'metrics': {
                'payback_simple_years': 7.1, 'payback_discounted_years': 8.4,
                'irr': 0.12, 'npv_eur': 4300.0, 'lcoe_eur_kwh': 0.08,
                'co2_avoided_year1_kg': 2100.0,
            },
            'incentives': {'total_eur': 1500.0},
        }
        db.session.add(scenario)
        db.session.commit()


class SeedTest(_Base):
    def test_seed_creates_all_with_correct_tags(self):
        report = DocumentBankSeeder.seed()
        self.assertEqual(report['created'], len(OFFICIAL_TEMPLATES_ES))
        self.assertEqual(report['skipped'], 0)

        templates = ReportTemplate.query.filter(
            ReportTemplate.org_id.is_(None), ReportTemplate.scope == 'system').all()
        self.assertEqual(len(templates), len(OFFICIAL_TEMPLATES_ES))

        by_name = {t.name: t for t in templates}
        for spec in OFFICIAL_TEMPLATES_ES:
            tpl = by_name[spec['name']]
            self.assertEqual(tpl.kind, spec['kind'])
            self.assertEqual(tpl.country, 'ES')
            self.assertEqual(tpl.required_by, spec['required_by'])
            self.assertEqual(tpl.stage, spec['stage'])
            self.assertTrue(tpl.is_official)
            self.assertEqual(tpl.status, 'published')
            self.assertTrue(tpl.is_system)
            self.assertIsNotNone(tpl.published_version)

    def test_seed_is_idempotent(self):
        first = DocumentBankSeeder.seed()
        second = DocumentBankSeeder.seed()
        self.assertEqual(first['created'], len(OFFICIAL_TEMPLATES_ES))
        self.assertEqual(second['created'], 0)
        self.assertEqual(second['skipped'], len(OFFICIAL_TEMPLATES_ES))
        self.assertEqual(
            ReportTemplate.query.filter(
                ReportTemplate.org_id.is_(None), ReportTemplate.scope == 'system').count(),
            len(OFFICIAL_TEMPLATES_ES))
        self.assertEqual(TemplateVersion.query.count(), len(OFFICIAL_TEMPLATES_ES))


class RenderTest(_Base):
    def test_every_template_renders_with_resolved_variables(self):
        DocumentBankSeeder.seed()
        templates = ReportTemplate.query.filter(
            ReportTemplate.org_id.is_(None), ReportTemplate.scope == 'system').all()
        for tpl in templates:
            version = tpl.published_version
            result = render_version(
                version.content, self.project, user=self.user, org=self.org,
                on_error='placeholder', presentation=tpl.presentation)
            html = result['html']
            self.assertIn('Cliente A', html, tpl.name)
            for entity in ('project', 'panel', 'inverter', 'battery', 'finance',
                           'installation', 'maintenance', 'incident', 'user', 'org'):
                self.assertNotIn(f'[{entity}.', html,
                                 f'{tpl.name}: variable sin resolver de {entity}')


class BankApiTest(_Base):
    def _login(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = self.org.id
        return client

    def test_bank_lists_official_templates(self):
        DocumentBankSeeder.seed()
        db.session.add(Flag(key='templates', nombre='Plantillas',
                            default_enabled=False, status='active'))
        db.session.add(FlagOverride(flag_key='templates', scope='org', scope_id=self.org.id,
                                    enabled=True, source='grant'))
        db.session.commit()

        client = self._login()
        resp = client.get('/api/templates/bank')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), len(OFFICIAL_TEMPLATES_ES))
        self.assertTrue(all(t['country'] == 'ES' and t['is_official'] for t in data))


if __name__ == '__main__':
    unittest.main()

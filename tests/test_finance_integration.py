"""Tests del módulo financiero: motor (payback/VAN/TIR/LCOE/CO2), CRUD de
escenarios, gating del flag y IDOR, más no-regresión del modelo de proyecto.

Motor: casos conocidos calculables a mano (TIR de [-1000,600,600] ≈ 0.13066,
signo del VAN, cashflow con degradación/escalada, contado vs financiado, y TIR
sin raíz devuelve None sin petar). Rutas: compute devuelve el desglose completo,
CRUD persiste, flag off -> 403 e IDOR -> 404.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.flag import Flag, FlagOverride
from app.models.financial_scenario import FinancialScenario
from app.schemas.finance import FinancialAssumptions, FinancingTerms
from app.services.finance import compute, irr, npv


class EngineMetricsTest(unittest.TestCase):
    def test_irr_known_case(self):
        rate = irr([-1000, 600, 600])
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 0.13066, places=4)

    def test_irr_no_root_returns_none(self):
        self.assertIsNone(irr([-1000, -100, -100]))
        self.assertIsNone(irr([1000, 100, 100]))

    def test_npv_sign(self):
        self.assertGreater(npv(0.05, [-1000, 600, 600]), 0)
        self.assertLess(npv(0.50, [-1000, 600, 600]), 0)

    def test_npv_zero_at_irr(self):
        rate = irr([-1000, 600, 600])
        self.assertAlmostEqual(npv(rate, [-1000, 600, 600]), 0.0, places=4)


class EngineComputeTest(unittest.TestCase):
    def _assumptions(self, **overrides):
        base = dict(
            capex_total=10000.0, iva_pct=0.0,
            tariff_eur_kwh=0.20, surplus_price_eur_kwh=0.05,
            annual_consumption_kwh=6000.0, lifetime_years=25,
            discount_rate=0.04, tariff_escalation_pct=0.0,
            panel_degradation_pct=0.0, om_cost_eur_year=0.0,
            emission_factor_kg_kwh=0.25,
        )
        base.update(overrides)
        return FinancialAssumptions(**base)

    def test_full_breakdown_keys(self):
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.6)
        for key in ('inputs', 'capex', 'annual_saving_year1_eur', 'metrics', 'cashflow'):
            self.assertIn(key, result)
        for key in ('payback_simple_years', 'payback_discounted_years', 'roi',
                    'irr', 'npv_eur', 'lcoe_eur_kwh', 'co2_avoided_year1_kg',
                    'co2_avoided_lifetime_kg'):
            self.assertIn(key, result['metrics'])
        self.assertEqual(len(result['cashflow']), 25)

    def test_year1_saving_and_surplus_cap(self):
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.6)
        self_kwh = 5000 * 0.6
        surplus_kwh = 5000 * 0.4
        grid_import = 6000 - self_kwh
        expected_self = self_kwh * 0.20
        expected_surplus = min(surplus_kwh * 0.05, grid_import * 0.20)
        self.assertAlmostEqual(result['annual_saving_year1_eur'],
                               round(expected_self + expected_surplus, 2), places=2)

    def test_co2_lifetime_no_degradation(self):
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.6)
        self.assertAlmostEqual(result['metrics']['co2_avoided_year1_kg'], 1250.0, places=1)
        self.assertAlmostEqual(result['metrics']['co2_avoided_lifetime_kg'], 1250.0 * 25, places=0)

    def test_degradation_and_escalation_shape(self):
        result = compute(
            self._assumptions(panel_degradation_pct=0.01, tariff_escalation_pct=0.03),
            production_kwh_year=5000.0, self_consumption_ratio=1.0)
        rows = result['cashflow']
        self.assertLess(rows[1]['production_kwh'], rows[0]['production_kwh'])
        self.assertGreater(rows[1]['tariff_eur_kwh'], rows[0]['tariff_eur_kwh'])

    def test_financed_vs_cash_initial_investment(self):
        cash = compute(self._assumptions(), production_kwh_year=5000.0,
                       self_consumption_ratio=0.7)
        financed = compute(
            self._assumptions(financing=FinancingTerms(amount=8000.0, interest_rate=0.05, term_years=10)),
            production_kwh_year=5000.0, self_consumption_ratio=0.7)
        self.assertGreater(cash['capex']['initial_investment_eur'],
                           financed['capex']['initial_investment_eur'])
        self.assertGreater(financed['cashflow'][0]['loan_payment_eur'], 0)
        self.assertEqual(financed['cashflow'][20]['loan_payment_eur'], 0)

    def test_incentive_reduces_net_capex(self):
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.7,
                         incentives=[{'kind': 'capex_reduction', 'amount': 3000.0}])
        self.assertAlmostEqual(result['capex']['net_eur'], 7000.0, places=2)
        self.assertAlmostEqual(result['capex']['incentive_reduction_eur'], 3000.0, places=2)

    def test_no_payback_returns_none(self):
        result = compute(self._assumptions(capex_total=1000000.0),
                         production_kwh_year=1000.0, self_consumption_ratio=0.5)
        self.assertIsNone(result['metrics']['payback_simple_years'])


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://',
                      WTF_CSRF_ENABLED=False)
    return app


class _RouteBase(unittest.TestCase):
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

        self.user_a = User(email='a@x.com', first_name='A', last_name='A', email_verified=True)
        self.user_a.set_password('x')
        self.user_b = User(email='b@x.com', first_name='B', last_name='B', email_verified=True)
        self.user_b.set_password('x')
        db.session.add_all([self.user_a, self.user_b])
        db.session.flush()

        db.session.add_all([
            Membership(user_id=self.user_a.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.user_b.id, org_id=self.org_b.id, role='owner'),
        ])

        self.project_a = Project(cliente='Cliente A', org_id=self.org_a.id, autoconsumo=60.0)
        self.project_a.resultados = {'annual_production': 5000.0}
        self.project_b = Project(cliente='Cliente B', org_id=self.org_b.id, autoconsumo=60.0)
        self.project_b.resultados = {'annual_production': 4000.0}
        db.session.add_all([self.project_a, self.project_b])

        db.session.add(Flag(key='finance', nombre='Finanzas', default_enabled=False, status='active'))
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _enable_flag(self, org):
        db.session.add(FlagOverride(flag_key='finance', scope='org', scope_id=org.id,
                                    enabled=True, source='grant'))
        db.session.commit()

    def _payload(self):
        return {'assumptions': {'capex_total': 10000.0, 'tariff_eur_kwh': 0.20,
                                'annual_consumption_kwh': 6000.0}}


class FlagGateTest(_RouteBase):
    def test_compute_flag_off_403(self):
        client = self._login(self.user_a, self.org_a)
        resp = client.post(f'/api/projects/{self.project_a.id}/financial/compute',
                           json=self._payload())
        self.assertEqual(resp.status_code, 403)

    def test_compute_flag_on_200(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        resp = client.post(f'/api/projects/{self.project_a.id}/financial/compute',
                           json=self._payload())
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('metrics', body)
        self.assertIn('irr', body['metrics'])
        self.assertEqual(len(body['cashflow']), 25)


class IdorTest(_RouteBase):
    def test_compute_other_org_project_404(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        resp = client.post(f'/api/projects/{self.project_b.id}/financial/compute',
                           json=self._payload())
        self.assertEqual(resp.status_code, 404)

    def test_scenario_other_org_404(self):
        self._enable_flag(self.org_a)
        self._enable_flag(self.org_b)
        client_b = self._login(self.user_b, self.org_b)
        created = client_b.post(
            f'/api/projects/{self.project_b.id}/financial/scenarios',
            json={'name': 'S', **self._payload()})
        self.assertEqual(created.status_code, 201)
        sid = created.get_json()['id']

        client_a = self._login(self.user_a, self.org_a)
        resp = client_a.get(
            f'/api/projects/{self.project_a.id}/financial/scenarios/{sid}')
        self.assertEqual(resp.status_code, 404)


class ScenarioCrudTest(_RouteBase):
    def test_crud_persists(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        base = f'/api/projects/{self.project_a.id}/financial/scenarios'

        created = client.post(base, json={'name': 'Contado', 'is_default': True, **self._payload()})
        self.assertEqual(created.status_code, 201)
        sid = created.get_json()['id']
        self.assertIsNotNone(created.get_json()['results']['metrics']['npv_eur'])

        listed = client.get(base)
        self.assertEqual(len(listed.get_json()), 1)

        patched = client.patch(f'{base}/{sid}', json={'name': 'Renombrado'})
        self.assertEqual(patched.get_json()['name'], 'Renombrado')

        deleted = client.delete(f'{base}/{sid}')
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(FinancialScenario.query.count(), 0)

    def test_default_is_exclusive(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        base = f'/api/projects/{self.project_a.id}/financial/scenarios'
        first = client.post(base, json={'name': 'A', 'is_default': True, **self._payload()}).get_json()
        second = client.post(base, json={'name': 'B', 'is_default': True, **self._payload()}).get_json()
        self.assertFalse(FinancialScenario.query.get(first['id']).is_default)
        self.assertTrue(FinancialScenario.query.get(second['id']).is_default)


class NoRegressionTest(_RouteBase):
    def test_project_to_dict_unaffected(self):
        d = self.project_a.to_dict()
        self.assertEqual(d['cliente'], 'Cliente A')
        self.assertEqual(d['resultados']['annual_production'], 5000.0)


if __name__ == '__main__':
    unittest.main()

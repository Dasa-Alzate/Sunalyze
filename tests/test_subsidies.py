"""Tests de subvenciones ES por capas y su integración con el motor financiero.

Resolución de incentivos: nacional solo (IRPF + Next Gen); nacional+CCAA+municipio acumulan;
IRPF con tope de base; IBI repartido en N años. Integración: con incentivos aplicados el
payback simple/descontado y la TIR mejoran frente a sin ellos, con los mismos supuestos.
Wiring de templates: el catálogo de propuesta_comercial incluye finance.* y render_version
resuelve {{ finance.payback_years }} con escenario y queda vacío sin escenario.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.financial_scenario import FinancialScenario
from app.schemas.finance import FinancialAssumptions
from app.services.finance import compute
from app.services.subsidies import SubsidyService, resolve
from app.services.subsidies import catalog as sub_catalog
from app.services.template_engine.catalog import variable_catalog
from app.services.template_engine import render_version


class ResolutionTest(unittest.TestCase):
    def test_national_only(self):
        incentives = SubsidyService.applicable(capex=12000.0, system_kwp=5.0)
        kinds = {i['label'].split(' ')[0] for i in incentives}
        self.assertTrue(any('IRPF' in i['label'] for i in incentives))
        self.assertTrue(any('Next' in i['label'] for i in incentives))
        self.assertFalse(any('IBI' in i['label'] for i in incentives))
        self.assertFalse(any('ICIO' in i['label'] for i in incentives))

    def test_irpf_base_cap(self):
        cfg = sub_catalog.NACIONAL['irpf']
        big = SubsidyService.applicable(capex=100000.0, system_kwp=0.0)
        irpf = next(i for i in big if 'IRPF' in i['label'])
        self.assertAlmostEqual(irpf['amount'], cfg['base_max'] * cfg['pct'], places=2)

    def test_next_gen_kwp_and_cap(self):
        small = SubsidyService.applicable(capex=100000.0, system_kwp=2.0)
        ng = next(i for i in small if 'Next' in i['label'])
        self.assertAlmostEqual(ng['amount'], 2.0 * 600.0, places=2)
        big = SubsidyService.applicable(capex=100000.0, system_kwp=20.0)
        ng_big = next(i for i in big if 'Next' in i['label'])
        self.assertAlmostEqual(ng_big['amount'], 3000.0, places=2)

    def test_layers_accumulate(self):
        national = SubsidyService.applicable(capex=12000.0, system_kwp=5.0)
        full = SubsidyService.applicable(capex=12000.0, system_kwp=5.0,
                                         ccaa='Comunidad Valenciana', municipio='Valencia')
        self.assertGreater(len(full), len(national))
        self.assertTrue(any('IBI' in i['label'] for i in full))
        self.assertTrue(any('ICIO' in i['label'] for i in full))

    def test_ibi_spread_over_years(self):
        full = SubsidyService.applicable(capex=12000.0, system_kwp=5.0, municipio='Valencia')
        ibi = [i for i in full if 'IBI' in i['label']]
        years = sorted(i['year'] for i in ibi)
        self.assertEqual(years, [1, 2, 3, 4, 5])
        for i in ibi:
            self.assertEqual(i['kind'], 'cashflow')

    def test_unknown_municipio_only_national(self):
        incentives = SubsidyService.applicable(capex=12000.0, system_kwp=5.0,
                                               municipio='Villarriba del Pisuerga')
        self.assertFalse(any('IBI' in i['label'] for i in incentives))

    def test_ccaa_adjusts_next_gen(self):
        rules = resolve(ccaa='Comunidad Valenciana')
        self.assertEqual(rules['next_gen']['eur_per_kwp'], 650.0)


class EngineIntegrationTest(unittest.TestCase):
    def _assumptions(self):
        return FinancialAssumptions(
            capex_total=12000.0, iva_pct=0.0,
            tariff_eur_kwh=0.20, surplus_price_eur_kwh=0.05,
            annual_consumption_kwh=6000.0, lifetime_years=25,
            discount_rate=0.04, tariff_escalation_pct=0.0,
            panel_degradation_pct=0.0, om_cost_eur_year=0.0,
        )

    def test_subsidies_improve_payback_and_irr(self):
        a = self._assumptions()
        without = compute(a, production_kwh_year=5000.0, self_consumption_ratio=0.7)
        incentives = SubsidyService.applicable(capex=12000.0, system_kwp=5.0,
                                               ccaa='Comunidad Valenciana', municipio='Valencia')
        with_subs = compute(a, production_kwh_year=5000.0, self_consumption_ratio=0.7,
                            incentives=incentives)

        self.assertGreater(with_subs['capex']['incentive_reduction_eur'], 0)
        self.assertLess(with_subs['capex']['net_eur'], without['capex']['net_eur'])
        self.assertLess(with_subs['metrics']['payback_simple_years'],
                        without['metrics']['payback_simple_years'])
        self.assertLess(with_subs['metrics']['payback_discounted_years'],
                        without['metrics']['payback_discounted_years'])
        self.assertGreater(with_subs['metrics']['irr'], without['metrics']['irr'])

    def test_incentives_breakdown_present(self):
        incentives = SubsidyService.applicable(capex=12000.0, system_kwp=5.0,
                                               municipio='Valencia')
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.7, incentives=incentives)
        self.assertIn('incentives', result)
        self.assertEqual(len(result['incentives']['items']), len(incentives))
        self.assertAlmostEqual(result['incentives']['total_eur'],
                               round(sum(i['amount'] for i in incentives), 2), places=2)

    def test_empty_incentives_breakdown(self):
        result = compute(self._assumptions(), production_kwh_year=5000.0,
                         self_consumption_ratio=0.7)
        self.assertEqual(result['incentives']['items'], [])
        self.assertEqual(result['incentives']['total_eur'], 0.0)


class TemplateCatalogTest(unittest.TestCase):
    def test_proposal_includes_finance(self):
        groups = variable_catalog('propuesta_comercial')
        entities = {g['entity'] for g in groups}
        self.assertIn('finance', entities)
        finance_group = next(g for g in groups if g['entity'] == 'finance')
        paths = {v['path'] for v in finance_group['vars']}
        for p in ('finance.payback_years', 'finance.net_capex', 'finance.irr',
                  'finance.incentives_total'):
            self.assertIn(p, paths)

    def test_other_kinds_have_no_finance(self):
        for kind in ('memoria_calculo', 'documento_legal', 'analisis_caso'):
            entities = {g['entity'] for g in variable_catalog(kind)}
            self.assertNotIn('finance', entities)


def _make_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://',
                      WTF_CSRF_ENABLED=False)
    return app


class TemplateRenderFinanceTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = Organization(nombre='Org', type='BUSINESS', plan='pro')
        db.session.add(self.org)
        db.session.flush()
        self.project = Project(cliente='C', org_id=self.org.id)
        db.session.add(self.project)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _section(self):
        return [{'id': 1, 'type': 'text', 'title': 'Propuesta',
                 'body': 'Payback: {{ finance.payback_years }} anos'}]

    def test_renders_finance_with_scenario(self):
        scenario = FinancialScenario(org_id=self.org.id, project_id=self.project.id,
                                     name='S', is_default=True)
        scenario.results = {
            'capex': {'net_eur': 9000.0},
            'metrics': {'payback_simple_years': 7.5, 'irr': 0.08, 'npv_eur': 4000.0},
            'annual_saving_year1_eur': 1200.0,
            'incentives': {'total_eur': 3000.0},
        }
        db.session.add(scenario)
        db.session.commit()

        out = render_version(self._section(), self.project, on_error='placeholder')
        self.assertIn('7.5', out['html'])
        self.assertNotIn('[finance.payback_years]', out['html'])

    def test_renders_empty_without_scenario(self):
        out = render_version(self._section(), self.project, on_error='placeholder')
        self.assertIn('Payback:  anos', out['html'])
        self.assertNotIn('[finance.payback_years]', out['html'])


if __name__ == '__main__':
    unittest.main()

"""Tests del motor de plantillas: resolución, cálculo, filtros y rechazo de input malicioso.

No requieren Flask ni base de datos: el resolver opera sobre objetos sencillos. Se centran en
la garantía de seguridad (no hay ejecución de código sobre el input del usuario).
"""

import unittest

from app.services.template_engine.parser import (
    parse_expression, evaluate, render_text,
)
from app.services.template_engine.context import ContextResolver
from app.services.template_engine.errors import TemplateError
from app.services.template_engine.filters import (
    filter_number, filter_thousands, filter_ellipsis, filter_upper, filter_lower,
    filter_money,
)
from app.services.template_engine.jurisdiction import resolve_jurisdiction
from app.models.report_template import DocumentKind, document_kind_var_groups


class _Box:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _resolver():
    context = {
        'project': _Box(cliente='ACME Solar', kwp=8.4, necesidad=5000),
        'panel': _Box(nombre='LR5-410', power=410.0, voc=37.2),
        'inverter': _Box(nombre='SUN2000', power=5.0, vmax=600),
        'wire': _Box(seccion=6.0, material='Cu', tipo='B1', corriente=40, no_conductores=2),
        'user': _Box(full_name='Ada Lovelace', first_name='Ada', last_name='Lovelace',
                     email='ada@example.com'),
        'org': _Box(nombre='Fleetx', type='BUSINESS', plan='pro'),
    }
    return ContextResolver(context)


class VariableResolutionTest(unittest.TestCase):
    def test_simple_path(self):
        r = _resolver()
        self.assertEqual(evaluate(parse_expression('project.cliente'), r), 'ACME Solar')
        self.assertEqual(evaluate(parse_expression('panel.power'), r), 410.0)
        self.assertEqual(evaluate(parse_expression('user.full_name'), r), 'Ada Lovelace')
        self.assertEqual(evaluate(parse_expression('org.nombre'), r), 'Fleetx')

    def test_unknown_entity_or_attr_raises(self):
        r = _resolver()
        with self.assertRaises(TemplateError):
            evaluate(parse_expression('banana.foo'), r)
        with self.assertRaises(TemplateError):
            evaluate(parse_expression('panel.precio'), r)

    def test_none_entity_yields_empty(self):
        r = ContextResolver({'project': None, 'panel': None, 'inverter': None,
                             'wire': None, 'user': None, 'org': None})
        self.assertEqual(render_text('valor={{ panel.power }}', r), 'valor=')

    def test_posventa_vars_resolve(self):
        context = {
            'installation': _Box(status='operativa', expected_annual_kwh=9000.0,
                                 commissioned_at=None, warranty_until=None, notes='ok'),
            'maintenance': _Box(kind='preventivo', status='realizada', scheduled_at=None,
                                done_at=None, technician='Bob', notes=''),
            'incident': _Box(title='Fallo string', description='', severity='alta',
                             status='abierta', opened_at=None, resolved_at=None),
        }
        r = ContextResolver(context)
        self.assertEqual(evaluate(parse_expression('installation.status'), r), 'operativa')
        self.assertEqual(evaluate(parse_expression('maintenance.technician'), r), 'Bob')
        self.assertEqual(evaluate(parse_expression('incident.title'), r), 'Fallo string')

    def test_posventa_vars_empty_without_installation(self):
        r = ContextResolver({'installation': None, 'maintenance': None, 'incident': None})
        self.assertEqual(render_text('{{ installation.status }}', r), '')
        self.assertEqual(render_text('{{ maintenance.technician }}', r), '')
        self.assertEqual(render_text('{{ incident.title }}', r), '')


class CalculationTest(unittest.TestCase):
    def test_arithmetic(self):
        r = _resolver()
        self.assertEqual(evaluate(parse_expression('2 + 3 * 4'), r), 14)
        self.assertEqual(evaluate(parse_expression('(2 + 3) * 4'), r), 20)
        self.assertEqual(evaluate(parse_expression('panel.power * 10'), r), 4100.0)

    def test_functions(self):
        r = _resolver()
        self.assertEqual(evaluate(parse_expression('round(3.14159, 2)'), r), 3.14)
        self.assertEqual(evaluate(parse_expression('sum(1, 2, 3)'), r), 6)
        self.assertEqual(evaluate(parse_expression('round(panel.power / 1000, 2)'), r), 0.41)

    def test_division_by_zero(self):
        r = _resolver()
        with self.assertRaises(TemplateError):
            evaluate(parse_expression('1 / 0'), r)


class FilterTest(unittest.TestCase):
    def test_number(self):
        self.assertEqual(filter_number(3.14159, 2), '3,14')
        self.assertEqual(filter_number(5, 0), '5')

    def test_thousands(self):
        self.assertEqual(filter_thousands(1234567.5, 2), '1.234.567,50')
        self.assertEqual(filter_thousands(1000, 0), '1.000')

    def test_ellipsis(self):
        self.assertEqual(filter_ellipsis('Hola mundo entero', 4), 'Hola…')
        self.assertEqual(filter_ellipsis('corto', 20), 'corto')

    def test_upper_lower(self):
        self.assertEqual(filter_upper('abc'), 'ABC')
        self.assertEqual(filter_lower('ABC'), 'abc')

    def test_pipeline(self):
        r = _resolver()
        self.assertEqual(evaluate(parse_expression('panel.power | number(1)'), r), '410,0')
        self.assertEqual(
            evaluate(parse_expression('project.cliente | upper | ellipsis(4)'), r), 'ACME…')

    def test_unknown_filter_raises(self):
        r = _resolver()
        with self.assertRaises(TemplateError):
            evaluate(parse_expression('panel.power | system'), r)


class I18nFilterTest(unittest.TestCase):
    def test_number_respects_locale(self):
        self.assertEqual(filter_number(1234.5, 2, presentation={'locale': 'es'}), '1234,50')
        self.assertEqual(filter_number(1234.5, 2, presentation={'locale': 'en'}), '1234.50')

    def test_thousands_respects_locale(self):
        self.assertEqual(
            filter_thousands(1234567.5, 2, presentation={'locale': 'es'}), '1.234.567,50')
        self.assertEqual(
            filter_thousands(1234567.5, 2, presentation={'locale': 'en'}), '1,234,567.50')

    def test_money_eur_vs_usd(self):
        eur = filter_money(1234.5, 2, presentation={'locale': 'es', 'currency': 'EUR'})
        usd = filter_money(1234.5, 2, presentation={'locale': 'en', 'currency': 'USD'})
        self.assertEqual(eur, '1.234,50 €')
        self.assertEqual(usd, '$1,234.50')

    def test_money_in_pipeline_reads_resolver_presentation(self):
        context = {'finance': _Box(net_capex=12000.0)}
        from app.services.template_engine.context import ContextResolver
        r_us = ContextResolver(context, presentation={'locale': 'en', 'currency': 'USD'})
        r_es = ContextResolver(context, presentation={'locale': 'es', 'currency': 'EUR'})
        self.assertEqual(evaluate(parse_expression('finance.net_capex | money'), r_us),
                         '$12,000.00')
        self.assertEqual(evaluate(parse_expression('finance.net_capex | money'), r_es),
                         '12.000,00 €')


class JurisdictionTest(unittest.TestCase):
    def test_country_drives_profile(self):
        self.assertEqual(resolve_jurisdiction('US'),
                         {'locale': 'en', 'currency': 'USD', 'page_size': 'Letter'})
        self.assertEqual(resolve_jurisdiction('ES'),
                         {'locale': 'es', 'currency': 'EUR', 'page_size': 'A4'})

    def test_default_is_es(self):
        self.assertEqual(resolve_jurisdiction(None)['currency'], 'EUR')
        self.assertEqual(resolve_jurisdiction('ZZ')['page_size'], 'A4')

    def test_explicit_overrides(self):
        prof = resolve_jurisdiction('US', currency='EUR')
        self.assertEqual(prof['currency'], 'EUR')
        self.assertEqual(prof['locale'], 'en')


class DocumentKindRegistryTest(unittest.TestCase):
    def test_new_kinds_present(self):
        for key in ('contrato', 'certificado', 'informe_mantenimiento', 'solicitud_conexion'):
            self.assertIn(key, DocumentKind.ALL)
            self.assertTrue(DocumentKind.is_valid(key))
            self.assertTrue(DocumentKind.label(key))

    def test_legacy_kinds_preserved(self):
        for key in ('memoria_calculo', 'documento_legal', 'propuesta_comercial', 'analisis_caso'):
            self.assertIn(key, DocumentKind.ALL)

    def test_var_groups_drive_catalog(self):
        from app.services.template_engine.catalog import variable_catalog
        groups = {g['entity'] for g in variable_catalog('certificado')}
        self.assertIn('installation', groups)
        self.assertIn('maintenance', groups)
        self.assertIn('incident', groups)
        self.assertNotIn('installation', document_kind_var_groups('memoria_calculo'))


class SecuritySSTITest(unittest.TestCase):
    """El input malicioso típico de SSTI debe ser rechazado, nunca ejecutado."""

    MALICIOUS = [
        '().__class__',
        "''.__class__.__mro__[1].__subclasses__()",
        'self.__init__.__globals__',
        'config',
        '__import__',
        'panel.__class__',
        'panel._sa_instance_state',
        'os.system',
    ]

    def test_malicious_expressions_rejected_at_parse(self):
        for expr in self.MALICIOUS:
            with self.subTest(expr=expr):
                raised = False
                try:
                    parsed = parse_expression(expr)
                    evaluate(parsed, _resolver())
                except TemplateError:
                    raised = True
                self.assertTrue(raised, f'No se rechazó input peligroso: {expr}')

    def test_dunder_rejected_in_render_safe_mode(self):
        r = _resolver()
        out = render_text('Hola {{ ().__class__ }}', r, on_error='placeholder')
        self.assertNotIn("<class", out)
        self.assertNotIn("type'", out)
        self.assertNotIn('subclass', out)
        self.assertEqual(out, 'Hola [().__class__]')

    def test_no_code_execution_side_effect(self):
        r = _resolver()
        for expr in self.MALICIOUS:
            render_text('{{ ' + expr + ' }}', r, on_error='placeholder')


if __name__ == '__main__':
    unittest.main()

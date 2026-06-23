"""Tests del motor de diagramas: geometria de puertos, connect(), plantillas y API."""

import types
import unittest

from app import create_app
from app.extensions import db
from app.services.circuit import CircuitService
from app.services.circuit.components import Fuse, Inverter
from app.services.circuit.core.diagram import Diagram
from app.services.circuit.core.geometry import rotate_point


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


def _config():
    return CircuitService.config_from_dict({
        'panel_model': 'PanelX', 'panel_voc': 40, 'panel_isc': 10,
        'panels_per_string': 8, 'num_strings': 2,
        'dc_fuse_i': 12, 'dc_switch_v': 1000, 'dc_cable_section': '6 mm2',
        'inverter_model': 'INV', 'inverter_power': 5, 'inverter_output_i': 22,
        'ac_phases': 1, 'ac_mcb_i': 25, 'ac_rcd_i': 25,
        'has_battery': True, 'battery_model': 'BATX',
    })


class GeometryTest(unittest.TestCase):
    def test_rotate_point_around_centre(self):
        self.assertEqual(rotate_point(60, 0, 0), (60, 0))
        self.assertEqual(rotate_point(60, 0, 90), (120.0, 60.0))
        self.assertEqual(rotate_point(60, 0, 180), (60.0, 120.0))
        self.assertEqual(rotate_point(60, 0, 270), (0.0, 60.0))

    def test_fuse_connection_points_by_orientation(self):
        self.assertEqual(Fuse.connection_points(0), {'in': (60, 0), 'out': (60, 120)})
        self.assertEqual(Fuse.connection_points(90)['out'], (0.0, 60.0))
        self.assertEqual(Fuse.connection_points(180), {'in': (60.0, 120.0), 'out': (60.0, 0.0)})
        self.assertEqual(Fuse.connection_points(270)['in'], (0.0, 60.0))

    def test_inverter_named_ports(self):
        p0 = Inverter.connection_points(0)
        self.assertEqual(p0['dc_in'], (60, 0))
        self.assertEqual(p0['ac_out'], (60, 120))
        p90 = Inverter.connection_points(90)
        self.assertEqual(p90['dc_in'], (120.0, 60.0))
        self.assertEqual(p90['ac_out'], (0.0, 60.0))


class ConnectTest(unittest.TestCase):
    def test_connect_draws_wire_between_ports(self):
        d = Diagram(cols=2, rows=3)
        a = d.place(Fuse(), 0, 0)
        b = d.place(Fuse(), 0, 1)
        d.connect(a, 'out', b, 'in')
        svg = d.render()
        self.assertIn('<line', svg)

    def test_port_absolute_coordinate(self):
        d = Diagram(cols=2, rows=3)
        a = d.place(Fuse(), 1, 2)
        self.assertEqual(d.port(a, 'in'), (1.5, 2.0))
        self.assertEqual(d.port(a, 'out'), (1.5, 3.0))

    def test_unknown_port_raises(self):
        d = Diagram(cols=2, rows=2)
        a = d.place(Fuse(), 0, 0)
        with self.assertRaises(KeyError):
            d.port(a, 'nope')


class TemplatesTest(unittest.TestCase):
    def setUp(self):
        self.cfg = _config()

    def _valid(self, svg):
        return svg.startswith('<svg') and svg.rstrip().endswith('</svg>')

    def test_four_named_templates_valid(self):
        for name in ('solar-basico', 'solar-con-baterias',
                     'solar-sin-fusibles', 'solar-con-fusibles'):
            svg = CircuitService.generate_template(name, self.cfg)
            self.assertTrue(self._valid(svg), name)

    def test_fuse_option_toggles_symbol(self):
        sin = CircuitService.generate_template('solar-sin-fusibles', self.cfg)
        con = CircuitService.generate_template('solar-con-fusibles', self.cfg)
        self.assertNotIn('Fusible', sin)
        self.assertIn('Fusible', con)

    def test_battery_template_includes_battery(self):
        bat = CircuitService.generate_template('solar-con-baterias', self.cfg)
        self.assertTrue('BATX' in bat or 'Bateria' in bat)

    def test_list_templates_has_four_plus(self):
        names = [t['name'] for t in CircuitService.list_templates()]
        for n in ('solar-basico', 'solar-con-baterias',
                  'solar-sin-fusibles', 'solar-con-fusibles'):
            self.assertIn(n, names)
        self.assertGreaterEqual(len(names), 4)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.params = {
            'panel_model': 'PanelX', 'panel_voc': 40, 'panel_isc': 10,
            'panels_per_string': 8, 'num_strings': 2,
            'dc_fuse_i': 12, 'dc_switch_v': 1000, 'dc_cable_section': '6 mm2',
            'inverter_model': 'INV', 'inverter_power': 5, 'inverter_output_i': 22,
            'ac_phases': 1, 'ac_mcb_i': 25, 'ac_rcd_i': 25,
            'has_battery': 'true', 'battery_model': 'BATX',
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_templates_endpoint_lists_four_plus(self):
        r = self.client.get('/api/circuit/templates')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertGreaterEqual(len(data), 4)
        self.assertTrue(all('name' in t and 'label' in t for t in data))

    def test_each_named_template_serves_svg(self):
        for name in ('solar-basico', 'solar-con-baterias',
                     'solar-sin-fusibles', 'solar-con-fusibles'):
            r = self.client.get(f'/api/circuit/{name}', query_string=self.params)
            self.assertEqual(r.status_code, 200, name)
            self.assertEqual(r.mimetype, 'image/svg+xml', name)

    def test_cc_strings_alias_still_works(self):
        r = self.client.get('/api/circuit/cc-strings', query_string=self.params)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'image/svg+xml')


class CircuitValidationTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.valid = {
            'panel_model': 'PanelX', 'panel_voc': 40, 'panel_isc': 10,
            'panels_per_string': 8, 'num_strings': 2,
            'dc_fuse_i': 12, 'dc_switch_v': 1000, 'dc_cable_section': '6 mm2',
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _status(self, overrides):
        params = dict(self.valid)
        params.update(overrides)
        return self.client.get('/api/circuit/solar-basico', query_string=params).status_code

    def test_valid_params_serve_svg(self):
        r = self.client.get('/api/circuit/solar-basico', query_string=self.valid)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'image/svg+xml')

    def test_non_numeric_voc_rejected(self):
        self.assertEqual(self._status({'panel_voc': 'abc'}), 422)

    def test_negative_strings_rejected(self):
        self.assertEqual(self._status({'num_strings': -5}), 422)

    def test_zero_strings_rejected(self):
        self.assertEqual(self._status({'num_strings': 0}), 422)

    def test_out_of_range_voc_rejected(self):
        self.assertEqual(self._status({'panel_voc': 99999}), 422)

    def test_invalid_phases_rejected(self):
        self.assertEqual(self._status({'ac_phases': 2}), 422)

    def test_named_templates_without_params_keep_presence_check(self):
        for name in ('solar-basico', 'solar-con-baterias',
                     'solar-sin-fusibles', 'solar-con-fusibles'):
            r = self.client.get(f'/api/circuit/{name}')
            self.assertEqual(r.status_code, 422, name)

    def test_named_templates_with_valid_params_serve_svg(self):
        for name in ('solar-basico', 'solar-con-baterias',
                     'solar-sin-fusibles', 'solar-con-fusibles',
                     'cc-strings', 'grid-connection', 'full-system'):
            r = self.client.get(f'/api/circuit/{name}', query_string=self.valid)
            self.assertEqual(r.status_code, 200, name)


class MemoriaNoRegressionTest(unittest.TestCase):
    def test_build_circuit_svgs_returns_three(self):
        from app.services.memoria_service import MemoriaService

        panel = types.SimpleNamespace(nombre='PanelX', voc=40, isc=10)
        inverter = types.SimpleNamespace(nombre='INV', power=5, I_max_output=22)
        data = {
            'mppt_inputs': '2', 'panels_number': '16',
            'inverter_phases': '1', 'wire_dc_section': '6 mm2',
            'wire_ac_section': '6 mm2',
        }
        out = MemoriaService._build_circuit_svgs(data, panel, inverter, battery=None)
        self.assertEqual(set(out), {'svg_cc', 'svg_ca', 'svg_sistema'})
        for v in out.values():
            self.assertIn('<svg', v)
            self.assertIn('</svg>', v)


if __name__ == '__main__':
    unittest.main()

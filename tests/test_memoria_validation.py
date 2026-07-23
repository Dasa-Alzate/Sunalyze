
import hashlib
import types
import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.installation_defaults import InstallationDefaults


def _weasyprint_available():
    try:
        from weasyprint import HTML
        HTML(string='<p>x</p>').write_pdf()
        return True
    except Exception:
        return False


WEASYPRINT_OK = _weasyprint_available()


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class MemoriaRouteValidationTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed()
        self.client = self._login()

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
        self.panel = Panel(nombre='LR5-410', voc=37.2, vmp=31.0, imp=13.2, isc=13.9, power=410.0)
        self.inverter = Inverter(nombre='SUN2000', power=5.0, vmax=600.0, I_max_output=24.0)
        db.session.add_all([self.panel, self.inverter])
        db.session.add(InstallationDefaults(
            dc_material='Cu', dc_modelo='H1Z2Z2-K', ac_material='Cu', ac_modelo='RZ1-K',
            tierra_material='Cu', tierra_modelo='H07V-K',
            dc_sobretensiones_modelo='SPD', dc_fusibles_modelo='gPV', dc_portafusibles='PF',
            dc_magnetotermico_modelo='MT', ac_diferencial_modelo='DIF',
            ac_magnetotermico_modelo='MT-AC', inyeccion_cero_modelo='IC', dispositivo_medida_modelo='DM'))
        db.session.commit()

    def _login(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = self.org.id
        return client

    def _valid_form(self):
        return {
            'location': 'Alicante', 'client_name': 'ACME', 'address': 'Calle 1',
            'zipcode': '03001', 'catastral_reference': 'REF123',
            'energy_company_name': 'Iberdrola', 'energy_company_cups': 'ES0021',
            'hired_power_kw': '5.75', 'input_v': '230', 'input_v_type': 'Monofasica',
            'inyection_type': 'Con inyeccion', 'panels_peak_power_kw': '6.5',
            'panels_number': '16', 'panels_place': 'Cubierta', 'panels_disposition': 'Coplanar',
            'inverter_place': 'Pared', 'wire_ground_length': '10',
            'protections_dc_thermal_v_max': '600', 'protections_dc_breaker_i': '16',
            'protections_ac_thermal_i': '16', 'protections_ac_diff_i': '25',
            'protections_ac_transitory_surge_model': 'Citel', 'mppt_inputs': '2',
            'panel_id': str(self.panel.id), 'inverter_id': str(self.inverter.id),
            'inverter_phases': '1', 'latitude': '38.34', 'longitude': '-0.48',
        }

    def _post(self, overrides=None):
        form = self._valid_form()
        if overrides:
            form.update(overrides)
        return self.client.post('/imprimir/memoria-pdf', data=form)

    def test_non_numeric_power_rejected(self):
        self.assertEqual(self._post({'hired_power_kw': 'abc'}).status_code, 422)

    def test_negative_power_rejected(self):
        self.assertEqual(self._post({'hired_power_kw': '-5'}).status_code, 422)

    def test_zero_panels_rejected(self):
        self.assertEqual(self._post({'panels_number': '0'}).status_code, 422)

    def test_bad_panel_id_rejected(self):
        self.assertEqual(self._post({'panel_id': '0'}).status_code, 422)
        self.assertEqual(self._post({'panel_id': '-3'}).status_code, 422)
        self.assertEqual(self._post({'panel_id': 'abc'}).status_code, 422)

    def test_latitude_out_of_range_rejected(self):
        self.assertEqual(self._post({'latitude': '200'}).status_code, 422)

    def test_longitude_out_of_range_rejected(self):
        self.assertEqual(self._post({'longitude': '-999'}).status_code, 422)

    def test_current_out_of_range_rejected(self):
        self.assertEqual(self._post({'protections_ac_diff_i': '99999'}).status_code, 422)

    def test_422_reports_field_errors(self):
        r = self._post({'hired_power_kw': 'abc', 'latitude': '200'})
        self.assertEqual(r.status_code, 422)
        body = r.get_json()
        self.assertEqual(body['code'], 'error.validation')
        fields = {d['field'] for d in body['details']}
        self.assertIn('hired_power_kw', fields)
        self.assertIn('latitude', fields)

    def test_missing_required_still_422(self):
        r = self._post({'client_name': ''})
        self.assertEqual(r.status_code, 422)

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint no disponible')
    def test_valid_form_produces_pdf(self):
        r = self._post()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/pdf')
        self.assertTrue(r.data.startswith(b'%PDF'))


class CircuitSvgByteNoRegressionTest(unittest.TestCase):

    EXPECTED = {
        'svg_cc': (5917, '9697786b49444a83f88bae9de4d19aac'),
        'svg_ca': (10487, '9bce08b8e47e7ebfbe0e5a9eebe58f6d'),
        'svg_sistema': (14929, '149882399fc7f9a9e6456a0b74defc6a'),
    }

    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_three_svgs_byte_identical(self):
        from app.services.memoria_service import MemoriaService

        panel = types.SimpleNamespace(nombre='PanelX', voc=40, isc=10)
        inverter = types.SimpleNamespace(nombre='INV', power=5, I_max_output=22)
        data = {
            'mppt_inputs': '2', 'panels_number': '16', 'inverter_phases': '1',
            'wire_dc_section': '6 mm2', 'wire_ac_section': '6 mm2',
        }
        out = MemoriaService._build_circuit_svgs(data, panel, inverter, battery=None)
        for key, (size, digest) in self.EXPECTED.items():
            raw = out[key].encode()
            self.assertEqual(len(raw), size, key)
            self.assertEqual(hashlib.md5(raw).hexdigest(), digest, key)


if __name__ == '__main__':
    unittest.main()

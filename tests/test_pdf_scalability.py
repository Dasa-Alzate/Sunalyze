
import os
import tempfile
import unittest
import uuid
from unittest import mock

from app import create_app
from app.extensions import db
from app.gateways.storage import get_storage, LocalStorage
from app.gateways.storage.s3 import S3Storage
from app.gateways.queue import (
    get_queue, SyncQueue, STATUS_QUEUED, STATUS_FINISHED, STATUS_NOT_FOUND,
)
from app.gateways.queue.base import JobQueue
from app.gateways.queue.rq_queue import RQQueue
from app.jobs import JOB_REGISTRY, resolve_job

from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.installation_defaults import InstallationDefaults
from app.models.flag import Flag, FlagOverride
from app.models.report_template import DocumentKind
from app.services.template_service import TemplateService


def _weasyprint_available():
    try:
        from weasyprint import HTML
        HTML(string='<p>x</p>').write_pdf()
        return True
    except Exception:
        return False


WEASYPRINT_OK = _weasyprint_available()


def _make_app(overrides=None):
    config = {'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True,
              'WTF_CSRF_ENABLED': False}
    if overrides:
        config.update(overrides)
    return create_app(config)


class FakeAsyncQueue(JobQueue):

    is_async = True

    def __init__(self):
        self._results = {}
        self._status = {}

    def enqueue(self, job_name, **kwargs):
        job_id = uuid.uuid4().hex
        self._results[job_id] = resolve_job(job_name)(**kwargs)
        self._status[job_id] = STATUS_QUEUED
        return job_id

    def finish(self, job_id):
        self._status[job_id] = STATUS_FINISHED

    def get_status(self, job_id):
        return self._status.get(job_id, STATUS_NOT_FOUND)

    def get_result(self, job_id):
        return self._results.get(job_id)


class LocalStorageTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.tmp = tempfile.TemporaryDirectory()
        self.app.instance_path = self.tmp.name
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        self.tmp.cleanup()

    def test_save_read_exists_roundtrip(self):
        storage = LocalStorage()
        ref = storage.save(7, 'abc.pdf', b'%PDF-hello')
        self.assertEqual(ref, os.path.join('generated', '7', 'abc.pdf'))
        self.assertTrue(storage.exists(ref))
        self.assertEqual(storage.read(ref), b'%PDF-hello')
        abs_path = os.path.join(self.app.instance_path, ref)
        self.assertTrue(os.path.isfile(abs_path))

    def test_read_missing_raises_filenotfound(self):
        storage = LocalStorage()
        with self.assertRaises(FileNotFoundError):
            storage.read('generated/7/missing.pdf')
        self.assertFalse(storage.exists('generated/7/missing.pdf'))

    def test_url_is_none_for_local(self):
        self.assertIsNone(LocalStorage().url('generated/1/x.pdf'))


class StorageSelectionTest(unittest.TestCase):
    def test_default_is_local(self):
        app = _make_app()
        with app.app_context():
            self.assertIsInstance(get_storage(), LocalStorage)

    def test_s3_selected_without_boto3_import(self):
        app = _make_app({'STORAGE_BACKEND': 's3', 'S3_BUCKET': 'my-bucket',
                         'S3_PREFIX': 'generated'})
        with app.app_context():
            storage = get_storage()
        self.assertIsInstance(storage, S3Storage)
        self.assertEqual(storage._object_key(9, 'x.pdf'), 'generated/9/x.pdf')


class QueueSelectionTest(unittest.TestCase):
    def test_default_is_sync(self):
        app = _make_app()
        with app.app_context():
            queue = get_queue()
        self.assertIsInstance(queue, SyncQueue)
        self.assertFalse(queue.is_async)

    def test_rq_selected_without_rq_import(self):
        app = _make_app({'JOB_QUEUE': 'rq',
                         'JOB_QUEUE_REDIS_URL': 'redis://localhost:6379/0'})
        with app.app_context():
            queue = get_queue()
        self.assertIsInstance(queue, RQQueue)
        self.assertTrue(queue.is_async)


class SyncQueueTest(unittest.TestCase):
    def setUp(self):
        JOB_REGISTRY['__test_echo__'] = lambda value: {'echo': value}

    def tearDown(self):
        JOB_REGISTRY.pop('__test_echo__', None)

    def test_runs_inline_and_returns_result(self):
        queue = SyncQueue()
        job_id = queue.enqueue('__test_echo__', value=42)
        self.assertFalse(queue.is_async)
        self.assertEqual(queue.get_status(job_id), STATUS_FINISHED)
        self.assertEqual(queue.get_result(job_id), {'echo': 42})

    def test_exception_propagates(self):
        def _boom():
            raise RuntimeError('boom')

        JOB_REGISTRY['__test_boom__'] = _boom
        try:
            with self.assertRaises(RuntimeError):
                SyncQueue().enqueue('__test_boom__')
        finally:
            JOB_REGISTRY.pop('__test_boom__', None)


class _SeededBase(unittest.TestCase):
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
        self.org_b = Organization(nombre='Org B', type='BUSINESS', plan='pro')
        db.session.add_all([self.org, self.org_b])
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
        db.session.flush()
        self.project = Project(cliente='Cliente A', org_id=self.org.id,
                               panel_id=self.panel.id, inverter_id=self.inverter.id)
        db.session.add(self.project)
        db.session.add(Flag(key='templates', nombre='Plantillas',
                            default_enabled=False, status='active'))
        db.session.add(InstallationDefaults(
            dc_material='Cu', dc_modelo='H1Z2Z2-K', ac_material='Cu', ac_modelo='RZ1-K',
            tierra_material='Cu', tierra_modelo='H07V-K',
            dc_sobretensiones_modelo='SPD', dc_fusibles_modelo='gPV', dc_portafusibles='PF',
            dc_magnetotermico_modelo='MT', ac_diferencial_modelo='DIF',
            ac_magnetotermico_modelo='MT-AC', inyeccion_cero_modelo='IC',
            dispositivo_medida_modelo='DM'))
        db.session.commit()
        self.template = TemplateService.create_template(
            self.org.id, self.user.id, DocumentKind.MEMORIA_CALCULO, 'Memoria A',
            content=[{'id': 's1', 'type': 'text', 'title': 'Memoria de {{ project.cliente }}',
                      'body': 'Panel {{ panel.nombre }}.'}])
        TemplateService.publish(self.org.id, self.template.id)
        db.session.add(FlagOverride(flag_key='templates', scope='org', scope_id=self.org.id,
                                    enabled=True, source='grant'))
        db.session.commit()

    def _login(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = self.org.id
        return client


class AsyncDocumentFlowTest(_SeededBase):
    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas')
    def test_generate_returns_202_then_poll_finishes(self):
        fake = FakeAsyncQueue()
        client = self._login()
        with mock.patch('app.routes.templates.get_queue', return_value=fake):
            resp = client.post(f'/api/templates/{self.template.id}/generate',
                               json={'project_id': self.project.id})
            self.assertEqual(resp.status_code, 202)
            job_id = resp.get_json()['job_id']
            self.assertEqual(resp.get_json()['status'], STATUS_QUEUED)

            resp = client.get(f'/api/documents/jobs/{job_id}')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json()['status'], STATUS_QUEUED)
            self.assertIsNone(resp.get_json()['document'])

            fake.finish(job_id)
            resp = client.get(f'/api/documents/jobs/{job_id}')
            self.assertEqual(resp.status_code, 200)
            doc = resp.get_json()['document']
            self.assertEqual(len(doc['pdf_sha256']), 64)
            doc_id = doc['id']

        resp = client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.startswith(b'%PDF'))

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas')
    def test_job_status_idor_other_org_is_404(self):
        fake = FakeAsyncQueue()
        client = self._login()
        with mock.patch('app.routes.templates.get_queue', return_value=fake):
            resp = client.post(f'/api/templates/{self.template.id}/generate',
                               json={'project_id': self.project.id})
            job_id = resp.get_json()['job_id']
            fake.finish(job_id)
            fake._results[job_id]['org_id'] = self.org_b.id
            resp = client.get(f'/api/documents/jobs/{job_id}')
            self.assertEqual(resp.status_code, 404)


class AsyncMemoriaFlowTest(_SeededBase):
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

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas')
    def test_memoria_returns_202_then_poll_streams_pdf(self):
        fake = FakeAsyncQueue()
        client = self._login()
        with mock.patch('app.routes.main.get_queue', return_value=fake):
            resp = client.post('/imprimir/memoria-pdf', data=self._valid_form())
            self.assertEqual(resp.status_code, 202)
            job_id = resp.get_json()['job_id']

            resp = client.get(f'/imprimir/memoria-pdf/jobs/{job_id}')
            self.assertEqual(resp.status_code, 202)

            fake.finish(job_id)
            resp = client.get(f'/imprimir/memoria-pdf/jobs/{job_id}')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.mimetype, 'application/pdf')
            self.assertTrue(resp.data.startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()

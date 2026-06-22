"""Tests de posventa: creacion de instalacion desde proyecto aprobado (y no
aprobado -> Conflict), transicion de estado, CRUD de visita/incidencia/lectura,
resumen esperado-vs-real, gating del flag (off -> 403), IDOR (otra org -> 404) y
no-regresion del modelo de proyecto.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.flag import Flag, FlagOverride
from app.models.installation import (
    Installation, MaintenanceVisit, Incident, ProductionReading,
)
from app.services.installation_service import InstallationService
from app.errors import Conflict


def _make_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://',
                      WTF_CSRF_ENABLED=False)
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

        self.project_a = Project(cliente='Cliente A', org_id=self.org_a.id, estado='aprobado')
        self.project_a.resultados = {'annual_production': 5000.0}
        self.project_draft = Project(cliente='Borrador', org_id=self.org_a.id, estado='borrador')
        self.project_b = Project(cliente='Cliente B', org_id=self.org_b.id, estado='aprobado')
        self.project_b.resultados = {'annual_production': 4000.0}
        db.session.add_all([self.project_a, self.project_draft, self.project_b])

        db.session.add(Flag(key='posventa', nombre='Posventa', default_enabled=False, status='active'))
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _enable_flag(self, org):
        db.session.add(FlagOverride(flag_key='posventa', scope='org', scope_id=org.id,
                                    enabled=True, source='grant'))
        db.session.commit()


class ServiceTest(_Base):
    def test_create_from_approved_project_with_baseline(self):
        inst = InstallationService.create_from_project(self.org_a.id, self.project_a.id)
        self.assertEqual(inst.status, 'operativa')
        self.assertEqual(inst.expected_annual_kwh, 5000.0)
        self.assertEqual(inst.project_id, self.project_a.id)

    def test_create_from_non_approved_raises_conflict(self):
        with self.assertRaises(Conflict):
            InstallationService.create_from_project(self.org_a.id, self.project_draft.id)

    def test_create_twice_raises_conflict(self):
        InstallationService.create_from_project(self.org_a.id, self.project_a.id)
        with self.assertRaises(Conflict):
            InstallationService.create_from_project(self.org_a.id, self.project_a.id)

    def test_set_status(self):
        inst = InstallationService.create_from_project(self.org_a.id, self.project_a.id)
        InstallationService.set_status(inst, 'mantenimiento')
        self.assertEqual(Installation.query.get(inst.id).status, 'mantenimiento')

    def test_performance_summary(self):
        inst = InstallationService.create_from_project(self.org_a.id, self.project_a.id)
        InstallationService.add_reading(inst, {'period': '2026-01', 'actual_kwh': 1000.0})
        InstallationService.add_reading(inst, {'period': '2026-02', 'actual_kwh': 1500.0})
        summary = InstallationService.performance_summary(inst)
        self.assertEqual(summary['actual_total_kwh'], 2500.0)
        self.assertEqual(summary['expected_annual_kwh'], 5000.0)
        self.assertEqual(summary['ratio'], 0.5)
        self.assertEqual(summary['reading_count'], 2)
        self.assertIn('method_note', summary)


class RouteCrudTest(_Base):
    def _create_installation(self, client):
        resp = client.post('/api/installations', json={'project_id': self.project_a.id})
        self.assertEqual(resp.status_code, 201)
        return resp.get_json()['id']

    def test_create_and_nested_crud_persists(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        iid = self._create_installation(client)

        patched = client.patch(f'/api/installations/{iid}', json={'status': 'incidencia'})
        self.assertEqual(patched.get_json()['status'], 'incidencia')

        v = client.post(f'/api/installations/{iid}/maintenance',
                        json={'kind': 'preventivo', 'technician': 'Ana'})
        self.assertEqual(v.status_code, 201)
        vid = v.get_json()['id']
        vp = client.patch(f'/api/installations/{iid}/maintenance/{vid}',
                          json={'status': 'realizada'})
        self.assertEqual(vp.get_json()['status'], 'realizada')

        inc = client.post(f'/api/installations/{iid}/incidents',
                          json={'title': 'Inversor caido', 'severity': 'alta'})
        self.assertEqual(inc.status_code, 201)
        iid_inc = inc.get_json()['id']

        r = client.post(f'/api/installations/{iid}/readings',
                        json={'period': '2026-03', 'actual_kwh': 800.0})
        self.assertEqual(r.status_code, 201)
        rid = r.get_json()['id']

        detail = client.get(f'/api/installations/{iid}').get_json()
        self.assertEqual(len(detail['maintenance']), 1)
        self.assertEqual(len(detail['incidents']), 1)
        self.assertEqual(len(detail['readings']), 1)
        self.assertEqual(detail['performance']['actual_total_kwh'], 800.0)

        self.assertEqual(MaintenanceVisit.query.count(), 1)
        self.assertEqual(Incident.query.count(), 1)
        self.assertEqual(ProductionReading.query.count(), 1)

        client.delete(f'/api/installations/{iid}/maintenance/{vid}')
        client.delete(f'/api/installations/{iid}/incidents/{iid_inc}')
        client.delete(f'/api/installations/{iid}/readings/{rid}')
        self.assertEqual(MaintenanceVisit.query.count(), 0)
        self.assertEqual(Incident.query.count(), 0)
        self.assertEqual(ProductionReading.query.count(), 0)

    def test_create_from_non_approved_returns_409(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        resp = client.post('/api/installations', json={'project_id': self.project_draft.id})
        self.assertEqual(resp.status_code, 409)


class FlagGateTest(_Base):
    def test_list_flag_off_403(self):
        client = self._login(self.user_a, self.org_a)
        resp = client.get('/api/installations')
        self.assertEqual(resp.status_code, 403)

    def test_create_flag_off_403(self):
        client = self._login(self.user_a, self.org_a)
        resp = client.post('/api/installations', json={'project_id': self.project_a.id})
        self.assertEqual(resp.status_code, 403)


class IdorTest(_Base):
    def test_get_other_org_installation_404(self):
        self._enable_flag(self.org_a)
        self._enable_flag(self.org_b)
        inst_b = InstallationService.create_from_project(self.org_b.id, self.project_b.id)
        client_a = self._login(self.user_a, self.org_a)
        resp = client_a.get(f'/api/installations/{inst_b.id}')
        self.assertEqual(resp.status_code, 404)

    def test_create_other_org_project_404(self):
        self._enable_flag(self.org_a)
        client_a = self._login(self.user_a, self.org_a)
        resp = client_a.post('/api/installations', json={'project_id': self.project_b.id})
        self.assertEqual(resp.status_code, 404)

    def test_nested_child_other_installation_404(self):
        self._enable_flag(self.org_a)
        self._enable_flag(self.org_b)
        inst_a = InstallationService.create_from_project(self.org_a.id, self.project_a.id)
        inst_b = InstallationService.create_from_project(self.org_b.id, self.project_b.id)
        visit_b = InstallationService.add_visit(inst_b, {'kind': 'preventivo'})
        client_a = self._login(self.user_a, self.org_a)
        resp = client_a.patch(
            f'/api/installations/{inst_a.id}/maintenance/{visit_b.id}',
            json={'status': 'realizada'})
        self.assertEqual(resp.status_code, 404)


class NoRegressionTest(_Base):
    def test_project_to_dict_unaffected(self):
        d = self.project_a.to_dict()
        self.assertEqual(d['cliente'], 'Cliente A')
        self.assertEqual(d['estado'], 'aprobado')
        self.assertEqual(d['resultados']['annual_production'], 5000.0)


if __name__ == '__main__':
    unittest.main()

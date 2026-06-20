"""Validacion de tipo y rango en creacion y actualizacion de proyectos.

Comprueba que el body se valida con el esquema pydantic (422 ante coordenadas o
potencias fuera de rango) y que un payload valido persiste (200/201), sin romper
los campos opcionales ausentes.
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
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
        self.user = User(email='a@example.com', first_name='Ana', last_name='Admin', email_verified=True)
        self.user.set_password('x')
        db.session.add(self.user)
        db.session.flush()
        db.session.add(Membership(user_id=self.user.id, org_id=self.org.id, role='owner'))
        db.session.commit()

    def _login(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['org_id'] = self.org.id
        return client


class CreateValidationTest(_Base):
    def test_latitud_out_of_range_is_422(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'C', 'latitud': 999})
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['code'], 'error.validation')

    def test_potencia_contratada_zero_is_422(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'C', 'potencia_contratada': 0})
        self.assertEqual(resp.status_code, 422)

    def test_non_numeric_latitud_is_422(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'C', 'latitud': 'norte'})
        self.assertEqual(resp.status_code, 422)

    def test_missing_cliente_is_422(self):
        client = self._login()
        resp = client.post('/api/projects', json={'direccion': 'Calle 1'})
        self.assertEqual(resp.status_code, 422)

    def test_valid_payload_persists(self):
        client = self._login()
        resp = client.post('/api/projects', json={
            'cliente': 'Cliente A', 'latitud': 40.4, 'longitud': -3.7,
            'potencia_contratada': 5.75, 'inclinacion': 30, 'azimut': 0,
            'resultados': {'total_field_power': 6.2},
        })
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body['latitud'], 40.4)
        self.assertEqual(body['kwp'], 6.2)
        stored = Project.query.get(body['id'])
        self.assertEqual(stored.potencia_contratada, 5.75)

    def test_empty_optional_string_becomes_none(self):
        client = self._login()
        resp = client.post('/api/projects', json={'cliente': 'C', 'direccion': '', 'panel_id': ''})
        self.assertEqual(resp.status_code, 201)
        self.assertIsNone(resp.get_json()['direccion'])
        self.assertIsNone(resp.get_json()['panel_id'])


class UpdateValidationTest(_Base):
    def _project(self):
        p = Project(cliente='Base', org_id=self.org.id)
        db.session.add(p)
        db.session.commit()
        return p

    def test_longitud_out_of_range_is_422(self):
        client = self._login()
        p = self._project()
        resp = client.patch(f'/api/projects/{p.id}', json={'longitud': -500})
        self.assertEqual(resp.status_code, 422)

    def test_valid_partial_update_persists(self):
        client = self._login()
        p = self._project()
        resp = client.patch(f'/api/projects/{p.id}', json={'direccion': 'Nueva 2', 'azimut': -45})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['direccion'], 'Nueva 2')
        self.assertEqual(resp.get_json()['azimut'], -45)
        self.assertEqual(resp.get_json()['cliente'], 'Base')


if __name__ == '__main__':
    unittest.main()

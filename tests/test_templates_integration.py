
import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.flag import Flag, FlagOverride
from app.models.report_template import (
    ReportTemplate, TemplateVersion, DocumentKind,
)
from app.services.template_service import TemplateService
from app.services.template_engine import render_version


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
        self.org_a = Organization(nombre='Org A', type='BUSINESS', plan='pro')
        self.org_b = Organization(nombre='Org B', type='BUSINESS', plan='pro')
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        self.user_a = User(email='a@example.com', first_name='Ana', last_name='Admin',
                           email_verified=True)
        self.user_a.set_password('x')
        self.user_b = User(email='b@example.com', first_name='Bob', last_name='Boss',
                           email_verified=True)
        self.user_b.set_password('x')
        db.session.add_all([self.user_a, self.user_b])
        db.session.flush()

        db.session.add_all([
            Membership(user_id=self.user_a.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.user_b.id, org_id=self.org_b.id, role='owner'),
        ])

        self.panel = Panel(nombre='LR5-410', voc=37.2, vmp=31.0, imp=13.2, power=410.0)
        self.inverter = Inverter(nombre='SUN2000', power=5.0, vmax=600.0)
        db.session.add_all([self.panel, self.inverter])
        db.session.flush()

        self.project_a = Project(cliente='Cliente A', org_id=self.org_a.id,
                                 panel_id=self.panel.id, inverter_id=self.inverter.id)
        db.session.add(self.project_a)

        flag = Flag(key='templates', nombre='Plantillas', default_enabled=False, status='active')
        db.session.add(flag)
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _enable_flag(self, org):
        db.session.add(FlagOverride(flag_key='templates', scope='org', scope_id=org.id,
                                    enabled=True, source='grant'))
        db.session.commit()


class RenderTest(_Base):
    def test_render_example_template(self):
        content = [
            {'id': 's1', 'type': 'text', 'title': 'Memoria de {{ project.cliente }}',
             'body': 'Panel {{ panel.nombre }} de {{ panel.power | number(0) }} W. '
                     'Potencia total {{ round(panel.power * 10 / 1000, 2) | number(2) }} kWp.'},
        ]
        result = render_version(content, self.project_a)
        html = result['html']
        self.assertIn('Memoria de Cliente A', html)
        self.assertIn('LR5-410', html)
        self.assertIn('410 W', html)
        self.assertIn('4,10 kWp', html)

    def test_render_escapes_html(self):
        self.project_a.cliente = '<script>alert(1)</script>'
        db.session.commit()
        result = render_version(
            [{'id': 's1', 'type': 'text', 'title': '', 'body': '{{ project.cliente }}'}],
            self.project_a)
        self.assertNotIn('<script>', result['html'])
        self.assertIn('&lt;script&gt;', result['html'])


class CrudLibraryTest(_Base):
    def test_create_update_content_publish(self):
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.MEMORIA_CALCULO, 'Plantilla 1',
            content=[{'id': 's1', 'type': 'text', 'title': 'T', 'body': '{{ project.cliente }}'}])
        self.assertEqual(tpl.latest_version.version, 1)

        version = TemplateService.save_content(
            self.org_a.id, tpl.id,
            [{'id': 's1', 'type': 'text', 'title': 'T2', 'body': 'x'}], changelog='cambio')
        self.assertEqual(version.version, 2)

        published = TemplateService.publish(self.org_a.id, tpl.id)
        self.assertEqual(published.status, 'published')
        self.assertIsNotNone(published.published_version)

    def test_install_favorite_uninstall(self):
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.DOCUMENTO_LEGAL, 'Legal')
        inst = TemplateService.install(self.org_a.id, tpl.id)
        self.assertEqual(len(TemplateService.list_library(self.org_a.id)), 1)

        inst = TemplateService.set_favorite(self.org_a.id, inst.id, True)
        self.assertTrue(inst.is_favorite)
        favs = TemplateService.list_library(self.org_a.id, favorite=True)
        self.assertEqual(len(favs), 1)

        TemplateService.uninstall(self.org_a.id, inst.id)
        self.assertEqual(len(TemplateService.list_library(self.org_a.id)), 0)
        self.assertIsNotNone(ReportTemplate.query.get(tpl.id))

    def test_install_system_template_does_not_delete_on_uninstall(self):
        system_tpl = ReportTemplate(org_id=None, scope='system', kind=DocumentKind.MEMORIA_CALCULO,
                                    name='Oficial', is_official=True, status='published')
        db.session.add(system_tpl)
        db.session.flush()
        db.session.add(TemplateVersion(template_id=system_tpl.id, version=1))
        db.session.commit()

        inst = TemplateService.install(self.org_a.id, system_tpl.id)
        TemplateService.uninstall(self.org_a.id, inst.id)
        self.assertIsNotNone(ReportTemplate.query.get(system_tpl.id))

    def test_categories_and_labels(self):
        cat = TemplateService.create_category(self.org_a.id, 'Residencial')
        label = TemplateService.create_label(self.org_a.id, 'urgente')
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.ANALISIS_CASO, 'A')
        inst = TemplateService.install(self.org_a.id, tpl.id)
        inst = TemplateService.set_category(self.org_a.id, inst.id, cat.id)
        self.assertEqual(inst.category_id, cat.id)
        inst = TemplateService.set_labels(self.org_a.id, inst.id, [label.id])
        self.assertEqual([l.name for l in inst.labels], ['urgente'])


class IsolationTest(_Base):
    def test_idor_other_org_template_is_404(self):
        from app.errors import NotFound
        tpl_b = TemplateService.create_template(
            self.org_b.id, self.user_b.id, DocumentKind.MEMORIA_CALCULO, 'B-only')
        with self.assertRaises(NotFound):
            TemplateService.update_template(self.org_a.id, tpl_b.id, name='hack')
        with self.assertRaises(NotFound):
            TemplateService.delete_template(self.org_a.id, tpl_b.id)
        with self.assertRaises(NotFound):
            TemplateService.save_content(self.org_a.id, tpl_b.id, [])

    def test_idor_other_org_installation_is_404(self):
        from app.errors import NotFound
        tpl_b = TemplateService.create_template(
            self.org_b.id, self.user_b.id, DocumentKind.MEMORIA_CALCULO, 'B')
        inst_b = TemplateService.install(self.org_b.id, tpl_b.id)
        with self.assertRaises(NotFound):
            TemplateService.uninstall(self.org_a.id, inst_b.id)
        with self.assertRaises(NotFound):
            TemplateService.set_favorite(self.org_a.id, inst_b.id, True)


class FlagGateTest(_Base):
    def test_routes_403_when_flag_off(self):
        client = self._login(self.user_a, self.org_a)
        resp = client.get('/api/templates')
        self.assertEqual(resp.status_code, 403)

    def test_routes_pass_when_flag_on(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        resp = client.get('/api/templates')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), [])

    def test_route_idor_returns_404_with_flag_on(self):
        self._enable_flag(self.org_a)
        self._enable_flag(self.org_b)
        tpl_b = TemplateService.create_template(
            self.org_b.id, self.user_b.id, DocumentKind.MEMORIA_CALCULO, 'B')
        client = self._login(self.user_a, self.org_a)
        resp = client.get(f'/api/templates/{tpl_b.id}')
        self.assertEqual(resp.status_code, 404)

    def test_route_create_and_preview_with_flag_on(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)
        resp = client.post('/api/templates', json={
            'kind': 'memoria_calculo', 'name': 'Memoria',
            'content': [{'id': 's1', 'type': 'text', 'title': 'T',
                         'body': 'Cliente: {{ project.cliente }}'}]})
        self.assertEqual(resp.status_code, 201)
        tpl_id = resp.get_json()['id']
        resp = client.post(f'/api/templates/{tpl_id}/preview',
                           json={'project_id': self.project_a.id})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Cliente A', resp.get_json()['html'])


if __name__ == '__main__':
    unittest.main()

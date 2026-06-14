"""Tests de integración del enganche a PDF de plantillas (GeneratedDocument).

Usa SQLite en memoria y el cliente de pruebas de Flask. Cubre: generar un PDF desde una
plantilla + proyecto (bytes que empiezan por %PDF, se crea GeneratedDocument con sha256 y
template_version_id fijado), listar los documentos de un proyecto, descarga (application/pdf),
aislamiento por org (IDOR -> 404 en doc y proyecto ajenos) y el gate del flag (apagado -> 403).

Si WeasyPrint no puede producir el PDF por falta de libs nativas, los tests que ejercitan
`write_pdf` se omiten (skip) tras verificar que el HTML ensamblado + el modelo + el wiring
están correctos; el resto de la cobertura no depende del motor nativo.
"""

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
    ReportTemplate, TemplateVersion, GeneratedDocument, DocumentKind,
)
from app.services.template_service import TemplateService
from app.services.document_service import DocumentService


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
        self.project_b = Project(cliente='Cliente B', org_id=self.org_b.id)
        db.session.add_all([self.project_a, self.project_b])

        flag = Flag(key='templates', nombre='Plantillas', default_enabled=False, status='active')
        db.session.add(flag)
        db.session.commit()

        self.template_a = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.MEMORIA_CALCULO, 'Memoria A',
            content=[{'id': 's1', 'type': 'text', 'title': 'Memoria de {{ project.cliente }}',
                      'body': 'Panel {{ panel.nombre }}.'}])
        TemplateService.publish(self.org_a.id, self.template_a.id)

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


class HtmlAssemblyTest(_Base):
    def test_build_document_html_pins_published_version(self):
        html, template, version, project = DocumentService.build_document_html(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        self.assertEqual(version.id, self.template_a.published_version.id)
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Memoria de Cliente A', html)
        self.assertIn('LR5-410', html)
        self.assertIn('@page', html)

    def test_es_render_is_default_no_regression(self):
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        self.assertIn('lang="es"', html)
        self.assertIn('size: A4', html)


class JurisdictionRenderTest(_Base):
    def _money_template(self, country=None, locale=None, currency=None):
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.PROPUESTA_COMERCIAL, 'Oferta',
            country=country, locale=locale, currency=currency,
            content=[{'id': 's1', 'type': 'text', 'title': 'Oferta',
                      'body': 'CAPEX {{ finance.net_capex | money }}'}])
        TemplateService.publish(self.org_a.id, tpl.id)
        return tpl

    def _seed_finance(self):
        from app.models.financial_scenario import FinancialScenario
        sc = FinancialScenario(
            org_id=self.org_a.id, project_id=self.project_a.id, name='base',
            is_default=True, results={'capex': {'net_eur': 12000.0}, 'metrics': {},
                                      'incentives': {}})
        db.session.add(sc)
        db.session.commit()

    def test_us_render_lang_letter_and_dollar(self):
        self._seed_finance()
        tpl = self._money_template(country='US')
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, tpl.id, self.project_a.id, user=self.user_a)
        self.assertIn('lang="en"', html)
        self.assertIn('size: Letter', html)
        self.assertIn('$12,000.00', html)

    def test_es_render_euro_and_a4(self):
        self._seed_finance()
        tpl = self._money_template(country='ES')
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, tpl.id, self.project_a.id, user=self.user_a)
        self.assertIn('lang="es"', html)
        self.assertIn('size: A4', html)
        self.assertIn('12.000,00 €', html)


class PosventaVarsRenderTest(_Base):
    def test_installation_vars_resolve_in_template(self):
        from app.models.installation import Installation
        inst = Installation(org_id=self.org_a.id, project_id=self.project_a.id,
                            status='operativa', expected_annual_kwh=9000.0)
        db.session.add(inst)
        db.session.commit()
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.CERTIFICADO, 'Cert',
            content=[{'id': 's1', 'type': 'text', 'title': 'Cert',
                      'body': 'Estado {{ installation.status }}'}])
        TemplateService.publish(self.org_a.id, tpl.id)
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, tpl.id, self.project_a.id, user=self.user_a)
        self.assertIn('Estado operativa', html)

    def test_installation_vars_empty_without_installation(self):
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.CERTIFICADO, 'Cert2',
            content=[{'id': 's1', 'type': 'text', 'title': 'Cert',
                      'body': 'Estado[{{ installation.status }}]'}])
        TemplateService.publish(self.org_a.id, tpl.id)
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, tpl.id, self.project_a.id, user=self.user_a)
        self.assertIn('Estado[]', html)


class BrandingRenderTest(_Base):
    def test_branding_applies_logo_color_footer(self):
        from app.models.organization import OrgBrandingProfile
        db.session.add(OrgBrandingProfile(
            org_id=self.org_a.id, logo_path='generated/a/logo.png',
            primary_color='#ff0000', footer_text='Mi pie legal'))
        db.session.commit()
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        self.assertIn('generated/a/logo.png', html)
        self.assertIn('#ff0000', html)
        self.assertIn('Mi pie legal', html)

    def test_no_branding_default_render(self):
        html, *_ = DocumentService.build_document_html(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        self.assertNotIn('<img class="tpl-logo"', html)
        self.assertNotIn('<footer class="tpl-footer"', html)


class TagColumnsTest(_Base):
    def test_tag_columns_persist_in_to_dict(self):
        tpl = TemplateService.create_template(
            self.org_a.id, self.user_a.id, DocumentKind.SOLICITUD_CONEXION, 'Conexion',
            country='ES', region='Madrid', required_by='distribuidora',
            stage='legalizacion', locale='es', currency='EUR')
        data = tpl.to_dict()
        self.assertEqual(data['required_by'], 'distribuidora')
        self.assertEqual(data['stage'], 'legalizacion')
        self.assertEqual(data['locale'], 'es')
        self.assertEqual(data['currency'], 'EUR')


class GenerateTest(_Base):
    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas (Pango)')
    def test_generate_creates_document_with_hash_and_pinned_version(self):
        doc = DocumentService.generate(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        self.assertEqual(doc.org_id, self.org_a.id)
        self.assertEqual(doc.template_version_id, self.template_a.published_version.id)
        self.assertEqual(doc.kind, DocumentKind.MEMORIA_CALCULO)
        self.assertEqual(len(doc.pdf_sha256), 64)
        self.assertGreater(doc.pdf_size_bytes, 0)
        self.assertEqual(doc.generated_by, self.user_a.id)

        _, pdf_bytes = DocumentService.read_pdf_bytes(self.org_a.id, doc.id)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
        import hashlib
        self.assertEqual(doc.pdf_sha256, hashlib.sha256(pdf_bytes).hexdigest())

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas (Pango)')
    def test_list_for_project(self):
        DocumentService.generate(
            self.org_a.id, self.template_a.id, self.project_a.id, user=self.user_a)
        docs = DocumentService.list_for_project(self.org_a.id, self.project_a.id)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['template_version'], self.template_a.published_version.version)


class IsolationTest(_Base):
    def test_idor_other_org_project_is_404(self):
        from app.errors import NotFound
        with self.assertRaises(NotFound):
            DocumentService.build_document_html(
                self.org_a.id, self.template_a.id, self.project_b.id)
        with self.assertRaises(NotFound):
            DocumentService.list_for_project(self.org_a.id, self.project_b.id)

    def test_idor_other_org_document_is_404(self):
        from app.errors import NotFound
        doc = GeneratedDocument(
            org_id=self.org_b.id, project_id=self.project_b.id,
            template_id=self.template_a.id,
            template_version_id=self.template_a.published_version.id,
            kind=DocumentKind.MEMORIA_CALCULO, pdf_path='generated/b/x.pdf',
            pdf_sha256='0' * 64, pdf_size_bytes=10, status='generated')
        db.session.add(doc)
        db.session.commit()
        with self.assertRaises(NotFound):
            DocumentService.get_document(self.org_a.id, doc.id)
        with self.assertRaises(NotFound):
            DocumentService.read_pdf_bytes(self.org_a.id, doc.id)


class RouteTest(_Base):
    def test_generate_403_when_flag_off(self):
        client = self._login(self.user_a, self.org_a)
        resp = client.post(f'/api/templates/{self.template_a.id}/generate',
                           json={'project_id': self.project_a.id})
        self.assertEqual(resp.status_code, 403)

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas (Pango)')
    def test_generate_list_download_flow_with_flag_on(self):
        self._enable_flag(self.org_a)
        client = self._login(self.user_a, self.org_a)

        resp = client.post(f'/api/templates/{self.template_a.id}/generate',
                           json={'project_id': self.project_a.id})
        self.assertEqual(resp.status_code, 201)
        doc_id = resp.get_json()['id']
        self.assertEqual(len(resp.get_json()['pdf_sha256']), 64)

        resp = client.get(f'/api/projects/{self.project_a.id}/documents')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()), 1)

        resp = client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/pdf')
        self.assertTrue(resp.data.startswith(b'%PDF'))

    @unittest.skipUnless(WEASYPRINT_OK, 'WeasyPrint requiere libs nativas (Pango)')
    def test_route_download_idor_returns_404(self):
        self._enable_flag(self.org_a)
        self._enable_flag(self.org_b)
        template_b = TemplateService.create_template(
            self.org_b.id, self.user_b.id, DocumentKind.MEMORIA_CALCULO, 'Memoria B',
            content=[{'id': 's1', 'type': 'text', 'title': 'T', 'body': 'x'}])
        TemplateService.publish(self.org_b.id, template_b.id)
        doc_b = DocumentService.generate(
            self.org_b.id, template_b.id, self.project_b.id, user=self.user_b)
        client = self._login(self.user_a, self.org_a)
        resp = client.get(f'/api/documents/{doc_b.id}/download')
        self.assertEqual(resp.status_code, 404)


if __name__ == '__main__':
    unittest.main()

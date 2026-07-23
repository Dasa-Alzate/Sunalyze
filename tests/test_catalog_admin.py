
import unittest

from app import create_app
from app.extensions import db
from app.models.catalog import Catalog
from app.models.organization import Organization
from app.models.user import User
from app.services.catalog_service import CatalogService


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class CatalogColumnsTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def test_new_columns_defaults_and_dict(self):
        c = Catalog(nombre='JA Solar', org_id=None, is_official=True, scraper_name='ja solar')
        db.session.add(c); db.session.commit()
        self.assertTrue(c.is_active)
        self.assertEqual(c.scraper_name, 'ja solar')
        d = c.to_dict()
        self.assertIn('scraper_name', d); self.assertIn('is_active', d)
        self.assertTrue(d['is_active'])


class VisibilityTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        self.org = Organization(nombre='O', type='BUSINESS', plan='pro')
        db.session.add(self.org); db.session.flush(); db.session.commit()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def test_official_catalog_creates_inactive(self):
        c = CatalogService.official_catalog('JA Solar', active=False)
        db.session.commit()
        self.assertFalse(c.is_active)
        self.assertEqual(c.scraper_name, 'ja solar')
        again = CatalogService.official_catalog('JA  Solar', active=False)
        self.assertEqual(again.id, c.id)

    def test_inactive_hidden_from_marketplace(self):
        CatalogService.official_catalog('JA Solar', active=False); db.session.commit()
        names = [c['nombre'] for c in CatalogService.marketplace(self.org.id)]
        self.assertNotIn('JA Solar', names)

    def test_active_visible_and_subscribable(self):
        c = CatalogService.official_catalog('Fronius', active=True); db.session.commit()
        names = [m['nombre'] for m in CatalogService.marketplace(self.org.id)]
        self.assertIn('Fronius', names)
        CatalogService.subscribe(self.org.id, c.id); db.session.commit()
        self.assertIn(c.id, CatalogService.visible_catalog_ids(self.org.id))


class CatalogAdminTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        self.su = User(email='su@x.com', first_name='S', last_name='U',
                       email_verified=True, is_superadmin=True)
        self.su.set_password('x'); db.session.add(self.su); db.session.commit()
        self.cat = CatalogService.official_catalog('Acme Solar', active=False); db.session.commit()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def _client(self):
        c = self.app.test_client()
        with c.session_transaction() as s:
            s['user_id'] = self.su.id
        return c

    def test_list_shows_inactive(self):
        r = self._client().get('/superadmin/catalogs')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Acme Solar', r.data)

    def test_activate(self):
        r = self._client().post(f'/superadmin/catalogs/{self.cat.id}/activate', data={'csrf_token': 'x'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Catalog.query.get(self.cat.id).is_active)


class CatalogMergeTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        from app.models.panel import Panel
        self.A = CatalogService.official_catalog('JA Solar', active=True)
        self.B = CatalogService.official_catalog('JASolar', active=False)
        db.session.commit()
        db.session.add(Panel(catalog_id=self.A.id, nombre='JA 450 oficial', power=450, voc=49, vmp=41, imp=11))
        db.session.add(Panel(catalog_id=self.B.id, nombre='JA dup distinto nombre', power=450, voc=49, vmp=41, imp=11))
        db.session.add(Panel(catalog_id=self.B.id, nombre='JA nuevo 500', power=500, voc=50, vmp=42, imp=12))
        db.session.commit()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def test_preview_classifies(self):
        from app.superadmin import catalog_admin
        prev = catalog_admin.merge_preview(self.B.id, self.A.id)
        self.assertEqual(len(prev['conflicts']), 1)
        self.assertEqual(len(prev['moves']), 1)

    def test_apply_keep_a_drops_dup_and_moves_new(self):
        from app.superadmin import catalog_admin
        from app.models.panel import Panel
        prev = catalog_admin.merge_preview(self.B.id, self.A.id)
        conflict_key = f"panel:{prev['conflicts'][0]['src']['id']}"
        res = catalog_admin.merge_apply(self.B.id, self.A.id, {conflict_key: 'keep_a'})
        self.assertEqual(res['moved'], 1)
        self.assertEqual(res['dropped'], 1)
        self.assertEqual(Panel.query.filter_by(catalog_id=self.A.id).count(), 2)
        self.assertTrue(Catalog.query.get(self.B.id).is_deleted)


if __name__ == '__main__':
    unittest.main()

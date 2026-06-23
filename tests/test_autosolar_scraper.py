"""Tests del scraper Autosolar: deducción de marca, parseo, enrutado y dedup."""

import os
import unittest

from app import create_app
from app.extensions import db
from app.scrapers.brands import normalize_brand, deduce_brand
from app.scrapers.base import NormalizedProduct

FIX = os.path.join(os.path.dirname(__file__), 'fixtures', 'autosolar')


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class BrandsTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_brand('JA  Solar'), 'ja solar')
        self.assertEqual(normalize_brand('JA-Solar'), 'ja solar')
        self.assertEqual(normalize_brand('Huawei'), 'huawei')
        self.assertEqual(normalize_brand(None), '')

    def test_deduce_from_attribute_new_brand(self):
        display, key = deduce_brand('Acme Solar', 'Panel Acme 450W')
        self.assertEqual(display, 'Acme Solar')
        self.assertEqual(key, 'acme solar')

    def test_deduce_known_from_title(self):
        display, key = deduce_brand(None, 'Inversor JASolar híbrido 5kW')
        self.assertEqual(display, 'JA Solar')
        self.assertEqual(key, 'ja solar')

    def test_deduce_none(self):
        self.assertEqual(deduce_brand(None, 'Cable rojo 6mm'), (None, None))


class NormalizedProductBrandTest(unittest.TestCase):
    def test_brand_default_and_set(self):
        p = NormalizedProduct(kind='panel', external_id='x')
        self.assertIsNone(p.brand)
        p2 = NormalizedProduct(kind='panel', external_id='x', brand='JA Solar')
        self.assertEqual(p2.brand, 'JA Solar')


class AutoSolarParseTest(unittest.TestCase):
    def _raw(self, name):
        with open(os.path.join(FIX, name), encoding='utf-8') as fh:
            return fh.read()

    def test_parse_panel_real_fixture(self):
        from app.scrapers.autosolar import AutoSolarScraper
        s = AutoSolarScraper()
        ref = {'external_id': 'pan1', 'url': 'http://a/pan1', 'kind': 'panel', 'nombre': ''}
        [p] = s.parse(ref, self._raw('panel.html'))
        self.assertEqual(p.kind, 'panel')
        self.assertEqual(p.brand, 'Tensite')
        self.assertEqual(p.fields['power'], 500.0)
        self.assertAlmostEqual(p.fields['voc'], 44.4)
        self.assertAlmostEqual(p.fields['vmp'], 37.05)
        self.assertAlmostEqual(p.fields['imp'], 13.5)
        self.assertAlmostEqual(p.fields['isc'], 14.25)
        self.assertIn('datasheet', p.fields)

    def test_watts_from_title_prefers_wattage_marker(self):
        from app.scrapers.autosolar import _watts_from_title
        self.assertEqual(_watts_from_title('Placa Solar 600W Bifacial Ja Solar'), 600.0)
        self.assertEqual(_watts_from_title('Panel Solar Flexible 240W 12V Tensite'), 240.0)
        self.assertEqual(_watts_from_title('Panel Solar 12V 150W'), 150.0)
        self.assertIsNone(_watts_from_title('Panel Solar Monocristalino Tensite'))

    def test_parse_inverter_real_fixture(self):
        from app.scrapers.autosolar import AutoSolarScraper
        s = AutoSolarScraper()
        ref = {'external_id': 'inv1', 'url': 'http://a/inv1', 'kind': 'inverter', 'nombre': ''}
        [p] = s.parse(ref, self._raw('inverter.html'))
        self.assertEqual(p.brand, 'Suntaic')
        self.assertEqual(p.fields['power'], 6.0)
        self.assertNotIn('vmax', p.fields)


class AutoSolarDiscoverTest(unittest.TestCase):
    def _raw(self, name):
        with open(os.path.join(FIX, name), encoding='utf-8') as fh:
            return fh.read()

    def test_discover_extracts_product_refs(self):
        from unittest.mock import patch, MagicMock
        from app.scrapers.autosolar import AutoSolarScraper
        s = AutoSolarScraper()
        s.max_products = 5
        html = self._raw('category_panels.html')

        def fake_get(url, **kwargs):
            resp = MagicMock()
            resp.text = html
            resp.raise_for_status = lambda: None
            return resp

        with patch('app.scrapers.autosolar.requests.get', side_effect=fake_get), \
             patch('app.scrapers.autosolar.time.sleep', lambda *_: None):
            refs = s.discover()
        self.assertEqual(len(refs), 5)
        self.assertTrue(all(r['kind'] == 'panel' for r in refs))
        self.assertTrue(all(r['url'].startswith('https://autosolar.es/') for r in refs))
        self.assertTrue(all(r['external_id'] for r in refs))


class _FakeScraper:
    brand = 'AutoSolar'
    requires_product_brand = True

    def __init__(self, products):
        self._p = products

    def discover(self):
        return [{'external_id': 'r1', 'url': 'http://x'}]

    def fetch(self, ref):
        return ''

    def parse(self, ref, raw):
        return self._p


class RoutingTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()

    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()

    def _run(self, products):
        from app.scrapers.service import ScraperService
        from app.scrapers import registry
        registry.SCRAPERS['fake'] = _FakeScraper(products)
        try:
            return ScraperService.run('fake')
        finally:
            registry.SCRAPERS.pop('fake', None)

    def _panel(self, **f):
        base = dict(nombre='X', power=450, voc=49, vmp=41, imp=11)
        base.update(f)
        return base

    def test_no_brand_rejected(self):
        from app.models.panel import Panel
        p = NormalizedProduct(kind='panel', external_id='r1', fields=self._panel(), brand=None)
        rep = self._run([p])
        self.assertEqual(Panel.query.count(), 0)
        self.assertTrue(any('marca' in b['reason'] for b in rep['blocked']))

    def test_new_brand_inactive_catalog(self):
        from app.models.panel import Panel
        from app.models.catalog import Catalog
        p = NormalizedProduct(kind='panel', external_id='r1',
                              fields=self._panel(nombre='Acme P1'), brand='Acme Solar')
        self._run([p])
        cat = Catalog.query.filter_by(scraper_name='acme solar').first()
        self.assertIsNotNone(cat); self.assertFalse(cat.is_active)
        self.assertEqual(Panel.query.filter_by(catalog_id=cat.id).count(), 1)

    def test_dedup_by_vitals_preserves_name(self):
        from app.models.panel import Panel
        p1 = NormalizedProduct(kind='panel', external_id='r1',
                               fields=self._panel(nombre='JA Solar 450 A'), brand='JA Solar')
        self._run([p1])
        p2 = NormalizedProduct(kind='panel', external_id='r2',
                               fields=self._panel(nombre='OTRO NOMBRE 450'), brand='JA Solar')
        self._run([p2])
        self.assertEqual(Panel.query.count(), 1)
        self.assertEqual(Panel.query.first().nombre, 'JA Solar 450 A')


if __name__ == '__main__':
    unittest.main()

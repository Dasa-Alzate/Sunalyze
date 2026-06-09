# Autosolar Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir un scraper del distribuidor Autosolar que enruta cada equipo al catálogo de su fabricante, con catálogos en cuarentena para marcas nuevas y un panel de superusuario para activarlos/mergearlos.

**Architecture:** Marca ≡ `Catalog` (con `scraper_name` + `is_active`). El servicio de scraping se generaliza para enrutar por producto (marca + tipo). Marca sin catálogo → catálogo `is_active=False` (invisible para usuarios). El superadmin server-rendered gestiona activación/CRUD/merge.

**Tech Stack:** Python 3 / Flask, SQLAlchemy, Flask-Migrate (Alembic), `requests` + `lxml`, Jinja (panel superadmin), unittest + SQLite en memoria.

## Global Constraints

- **Sin comentarios inline (`#`) en el código.** Solo docstrings de módulo/función al estilo del repo. (Preferencia inviolable de David.)
- Rama de feature `feat/autosolar-scraper`; nunca `main`.
- `Panel.nombre` / `Inverter.nombre` / `Battery.nombre` son `unique` global.
- Migración cuelga de head `73c21c5757c4`.
- Tests con `SQLALCHEMY_DATABASE_URI='sqlite://'`, patrón `_Base` de `tests/test_batteries_integration.py`.
- Comandos de test: `python -m pytest <ruta> -v` (o `python -m unittest`).

---

## File Structure

- `app/models/catalog.py` — + `scraper_name`, `is_active`, `to_dict`.
- `migrations/versions/<rev>_catalog_scraper_name_is_active.py` — nuevo.
- `app/scrapers/brands.py` — nuevo: normalización + deducción de marca.
- `app/scrapers/base.py` — + `NormalizedProduct.brand`.
- `app/services/catalog_service.py` — + `official_catalog`, filtros `is_active`.
- `app/scrapers/service.py` — enrutado por producto + dedup.
- `app/scrapers/autosolar.py` — nuevo scraper.
- `app/scrapers/registry.py` — registrar autosolar.
- `app/utils/data_loader.py` — usar `CatalogService.official_catalog`.
- `app/superadmin/catalog_admin.py` — nuevo: servicio de listado/CRUD/merge.
- `app/superadmin/views.py` — + rutas de catálogos.
- `app/superadmin/templates/superadmin/catalogs.html`, `catalog_detail.html`, `catalog_merge.html` — nuevos.
- `app/superadmin/templates/superadmin/base.html` — + entrada de nav.
- `tests/test_autosolar_scraper.py`, `tests/test_catalog_admin.py` — nuevos.
- `tests/fixtures/autosolar/panel.html`, `inverter.html` — nuevos.

---

### Task 1: Columnas `scraper_name` + `is_active` en `Catalog`

**Files:**
- Modify: `app/models/catalog.py:16-33`
- Create: `migrations/versions/a1b2c3d4e5f6_catalog_scraper_name_is_active.py`
- Test: `tests/test_catalog_admin.py`

**Interfaces:**
- Produces: `Catalog.scraper_name` (str|None), `Catalog.is_active` (bool, default True); `to_dict()` incluye ambos.

- [ ] **Step 1: Failing test**

```python
import unittest
from app import create_app
from app.extensions import db
from app.models.catalog import Catalog


def _make_app():
    app = create_app()
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
```

- [ ] **Step 2: Run, expect FAIL** — `python -m pytest tests/test_catalog_admin.py::CatalogColumnsTest -v` → falla (`is_active`/`scraper_name` no existen).

- [ ] **Step 3: Modify `app/models/catalog.py`**

Añadir tras `is_official` (línea 19):

```python
    scraper_name = db.Column(db.String(100), index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
```

En `to_dict()` añadir:

```python
            'scraper_name': self.scraper_name,
            'is_active': self.is_active,
```

- [ ] **Step 4: Create migration**

```python
"""catalog scraper_name + is_active

Revision ID: a1b2c3d4e5f6
Revises: 73c21c5757c4
Create Date: 2026-06-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '73c21c5757c4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('catalogs', sa.Column('scraper_name', sa.String(length=100), nullable=True))
    op.add_column('catalogs', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index('ix_catalogs_scraper_name', 'catalogs', ['scraper_name'])
    op.execute("UPDATE catalogs SET scraper_name = lower(nombre) WHERE org_id IS NULL AND is_official = 1 AND scraper_name IS NULL")


def downgrade():
    op.drop_index('ix_catalogs_scraper_name', table_name='catalogs')
    op.drop_column('catalogs', 'is_active')
    op.drop_column('catalogs', 'scraper_name')
```

- [ ] **Step 5: Run, expect PASS** — `python -m pytest tests/test_catalog_admin.py::CatalogColumnsTest -v`

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat(catalog): scraper_name + is_active"`

---

### Task 2: Deducción de marca (`brands.py`)

**Files:**
- Create: `app/scrapers/brands.py`
- Test: `tests/test_autosolar_scraper.py`

**Interfaces:**
- Produces:
  - `normalize_brand(raw: str|None) -> str` (minúsculas, sin acentos, espacios/guiones colapsados; `''` si vacío).
  - `KNOWN_BRANDS: dict[str,str]` (alias normalizado → display canónico).
  - `deduce_brand(attr: str|None, title: str|None) -> tuple[str|None, str|None]` → `(display, scraper_name)`.

- [ ] **Step 1: Failing test**

```python
import unittest
from app.scrapers.brands import normalize_brand, deduce_brand


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
```

- [ ] **Step 2: Run, expect FAIL** — `python -m pytest tests/test_autosolar_scraper.py::BrandsTest -v`

- [ ] **Step 3: Implement `app/scrapers/brands.py`**

```python
"""Deducción y canonicalización de marca para scrapers de distribuidores.

`scraper_name` es la clave normalizada con la que se busca/crea el catálogo de la
marca; `KNOWN_BRANDS` mapea variantes tipográficas a un display canónico para no
fragmentar catálogos por diferencias triviales.
"""

import re
import unicodedata


def normalize_brand(raw):
    if not raw:
        return ''
    text = unicodedata.normalize('NFKD', str(raw))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace('-', ' ').replace('_', ' ')
    return re.sub(r'\s+', ' ', text).strip()


KNOWN_BRANDS = {
    'ja solar': 'JA Solar',
    'jasolar': 'JA Solar',
    'huawei': 'Huawei',
    'fronius': 'Fronius',
    'victron': 'Victron Energy',
    'victron energy': 'Victron Energy',
    'pylontech': 'Pylontech',
    'longi': 'LONGi',
    'trina': 'Trina Solar',
    'trina solar': 'Trina Solar',
    'canadian solar': 'Canadian Solar',
    'sma': 'SMA',
    'growatt': 'Growatt',
}


def _canonical(display):
    key = normalize_brand(display)
    if key in KNOWN_BRANDS:
        canonical = KNOWN_BRANDS[key]
        return canonical, normalize_brand(canonical)
    return display.strip(), key


def deduce_brand(attr, title):
    if attr and attr.strip():
        return _canonical(attr)
    key = normalize_brand(title)
    for alias, canonical in KNOWN_BRANDS.items():
        if alias in key:
            return canonical, normalize_brand(canonical)
    return None, None
```

- [ ] **Step 4: Run, expect PASS** — `python -m pytest tests/test_autosolar_scraper.py::BrandsTest -v`

- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat(scraper): deducción de marca (brands.py)"`

---

### Task 3: `NormalizedProduct.brand`

**Files:**
- Modify: `app/scrapers/base.py:18-30`
- Test: `tests/test_autosolar_scraper.py`

**Interfaces:**
- Produces: `NormalizedProduct(kind, external_id, source_url='', fields={}, brand=None)`.

- [ ] **Step 1: Failing test**

```python
from app.scrapers.base import NormalizedProduct

class NormalizedProductBrandTest(unittest.TestCase):
    def test_brand_default_and_set(self):
        p = NormalizedProduct(kind='panel', external_id='x')
        self.assertIsNone(p.brand)
        p2 = NormalizedProduct(kind='panel', external_id='x', brand='JA Solar')
        self.assertEqual(p2.brand, 'JA Solar')
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Modify dataclass** — añadir tras `fields`:

```python
    brand: str = None
```

- [ ] **Step 4: Run, expect PASS**

- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat(scraper): NormalizedProduct.brand"`

---

### Task 4: `CatalogService.official_catalog` + filtros de visibilidad

**Files:**
- Modify: `app/services/catalog_service.py`
- Modify: `app/utils/data_loader.py:57-68` (usar el helper)
- Test: `tests/test_catalog_admin.py`

**Interfaces:**
- Consumes: `normalize_brand` (Task 2).
- Produces: `CatalogService.official_catalog(display_name, *, active=True) -> Catalog`. Filtros `is_active=True` en `own_catalog_ids`, `subscribed_catalog_ids`, `library`, `marketplace`, `bootstrap_org`.

- [ ] **Step 1: Failing test**

```python
from app.services.catalog_service import CatalogService
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.user import User

class VisibilityTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        self.org = Organization(nombre='O', type='BUSINESS', plan='pro'); db.session.add(self.org); db.session.flush()
        db.session.commit()

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
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement in `catalog_service.py`**

Importar arriba:

```python
from app.scrapers.brands import normalize_brand
```

Añadir método:

```python
    @staticmethod
    def official_catalog(display_name, *, active=True):
        """Catálogo oficial de una marca, localizado por scraper_name normalizado.

        Si no existe lo crea (marketplace, oficial). `active=False` lo deja en
        cuarentena: invisible para usuarios hasta que un superusuario lo active.
        """
        key = normalize_brand(display_name)
        catalog = Catalog.query.filter_by(scraper_name=key, org_id=None).first()
        if not catalog:
            catalog = Catalog(nombre=display_name.strip(), scraper_name=key,
                              descripcion=f'Catálogo oficial de {display_name.strip()}',
                              org_id=None, is_official=True, is_active=active)
            db.session.add(catalog)
            db.session.flush()
        return catalog
```

Añadir `Catalog.is_active.is_(True)` a:

- `own_catalog_ids` (línea 28-30): `.filter(Catalog.org_id == org_id, Catalog.deleted_at.is_(None), Catalog.is_active.is_(True))`
- `subscribed_catalog_ids` (línea 40): añadir `, Catalog.is_active.is_(True)`
- `library` query `own` (línea 74-76) y `subs` (línea 77-79): añadir `, Catalog.is_active.is_(True)`
- `marketplace` (línea 99-101): añadir `, Catalog.is_active.is_(True)`
- `bootstrap_org` (línea 174): `.filter(Catalog.org_id.is_(None), Catalog.is_official.is_(True), Catalog.is_active.is_(True))`

- [ ] **Step 4: Refactor `data_loader.py`** — reemplazar cuerpo de `_official_catalog`:

```python
def _official_catalog(brand):
    from app.services.catalog_service import CatalogService
    return CatalogService.official_catalog(brand, active=True)
```

- [ ] **Step 5: Run, expect PASS** — `python -m pytest tests/test_catalog_admin.py -v`

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat(catalog): official_catalog por scraper_name + ocultar inactivos"`

---

### Task 5: Enrutado por producto + dedup en `service.py`

**Files:**
- Modify: `app/scrapers/service.py`
- Test: `tests/test_autosolar_scraper.py`

**Interfaces:**
- Consumes: `NormalizedProduct.brand`, `CatalogService.official_catalog`, `scraper.requires_product_brand`.
- Produces: `ScraperService.run(brand, dry_run=False)` enruta por `product.brand`/`product.kind`; rechaza sin marca; dedup external_id → nombre global → vitales por marca (preserva nombre).

- [ ] **Step 1: Failing tests**

```python
from app.scrapers.base import NormalizedProduct
from app.scrapers.service import ScraperService
from app.scrapers import registry
from app.models.panel import Panel
from app.models.catalog import Catalog

class _FakeScraper:
    brand = 'AutoSolar'
    requires_product_brand = True
    def __init__(self, products): self._p = products
    def discover(self): return [{'external_id': 'r1', 'url': 'http://x'}]
    def fetch(self, ref): return ''
    def parse(self, ref, raw): return self._p

class RoutingTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
    def tearDown(self):
        db.session.remove(); db.drop_all(); self.ctx.pop()
    def _run(self, products):
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
        p = NormalizedProduct(kind='panel', external_id='r1', fields=self._panel(), brand=None)
        rep = self._run([p])
        self.assertEqual(Panel.query.count(), 0)
        self.assertTrue(any('marca' in b['reason'] for b in rep['blocked']))

    def test_new_brand_inactive_catalog(self):
        p = NormalizedProduct(kind='panel', external_id='r1', fields=self._panel(nombre='Acme P1'), brand='Acme Solar')
        self._run([p])
        cat = Catalog.query.filter_by(scraper_name='acme solar').first()
        self.assertIsNotNone(cat); self.assertFalse(cat.is_active)
        self.assertEqual(Panel.query.filter_by(catalog_id=cat.id).count(), 1)

    def test_dedup_by_vitals_preserves_name(self):
        p1 = NormalizedProduct(kind='panel', external_id='r1', fields=self._panel(nombre='JA Solar 450 A', power=450, voc=49, vmp=41, imp=11), brand='JA Solar')
        self._run([p1])
        p2 = NormalizedProduct(kind='panel', external_id='r2', fields=self._panel(nombre='OTRO NOMBRE 450', power=450, voc=49, vmp=41, imp=11), brand='JA Solar')
        self._run([p2])
        self.assertEqual(Panel.query.count(), 1)
        self.assertEqual(Panel.query.first().nombre, 'JA Solar 450 A')
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Rewrite `service.py`**

```python
"""Orquestación del scraping: discover → fetch → parse → upsert con provenance.

Enruta cada producto al catálogo de su marca (`product.brand`) y al modelo de su
tipo (`product.kind`). Si el scraper exige marca por producto (`requires_product_brand`)
y no se dedujo, el producto se rechaza. Dedup dentro de la marca: external_id →
nombre normalizado (consulta global por el unique) → vitales con tolerancia; en el
match por vitales sobrevive el nombre existente. `is_locked` nunca se pisa.
"""

import logging
from datetime import datetime

from app.extensions import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.scrape_run import ScrapeRun
from app.services.catalog_service import CatalogService
from app.scrapers.registry import get_scraper
from app.scrapers import acceptance
from app.scrapers.base import VITAL

logger = logging.getLogger(__name__)

_MODEL = {'panel': Panel, 'inverter': Inverter}
_VITAL_NUM = {'panel': ('power', 'voc', 'vmp', 'imp'), 'inverter': ('power', 'vmax')}
_TOL = 0.02


def _norm_name(name):
    return ' '.join((name or '').lower().split())


class ScraperService:

    @staticmethod
    def run(brand, dry_run=False):
        scraper = get_scraper(brand)
        if not scraper:
            raise ValueError(f'No hay scraper registrado para «{brand}».')

        report = {'brand': scraper.brand, 'dry_run': dry_run,
                  'created': [], 'updated': [], 'review': [], 'blocked': [],
                  'skipped': [], 'errors': []}
        catalog_cache = {}

        for ref in scraper.discover():
            try:
                raw = scraper.fetch(ref)
                products = scraper.parse(ref, raw)
            except Exception as exc:
                logger.exception('Fallo al obtener %s', ref.get('url'))
                report['errors'].append({'ref': ref.get('external_id'), 'error': str(exc)})
                continue

            for product in products:
                catalog_brand = product.brand or (
                    None if getattr(scraper, 'requires_product_brand', False) else scraper.brand)
                if not catalog_brand:
                    report['blocked'].append({'id': product.external_id, 'reason': 'sin marca deducida'})
                    continue
                if product.kind not in _MODEL:
                    report['blocked'].append({'id': product.external_id, 'reason': f'tipo no soportado: {product.kind}'})
                    continue

                verdict = acceptance.evaluate(product, catalog_brand)
                if verdict['verdict'] == 'blocked':
                    report['blocked'].append({'id': product.external_id, 'reason': '; '.join(verdict['block'])})
                    continue
                review_notes = '; '.join(verdict['review']) if verdict['verdict'] == 'review' else None

                if catalog_brand not in catalog_cache:
                    catalog_cache[catalog_brand] = CatalogService.official_catalog(catalog_brand, active=False)
                catalog = catalog_cache[catalog_brand]
                Model = _MODEL[product.kind]

                action = ScraperService._upsert(Model, catalog, catalog_brand, product, dry_run, review_notes)
                report[action['result']].append(action['detail'])
                if review_notes and action['result'] != 'blocked':
                    report['review'].append({'id': product.external_id, 'reason': review_notes})

        ScraperService._record_run(scraper.brand, dry_run, report)
        return report

    @staticmethod
    def _find_existing(Model, catalog, product):
        existing = Model.query.filter_by(catalog_id=catalog.id, external_id=product.external_id).first()
        if existing:
            return existing, 'external_id'
        nombre = product.fields.get('nombre')
        by_name = Model.query.filter_by(nombre=nombre).first() if nombre else None
        if by_name:
            return by_name, ('name' if by_name.catalog_id == catalog.id else 'name_other_catalog')
        match = ScraperService._match_by_vitals(Model, catalog, product)
        if match:
            return match, 'vitals'
        return None, None

    @staticmethod
    def _match_by_vitals(Model, catalog, product):
        fields = _VITAL_NUM[product.kind]
        target = {f: product.fields.get(f) for f in fields}
        if any(target[f] is None for f in fields):
            return None
        for row in Model.query.filter_by(catalog_id=catalog.id).all():
            ok = True
            for f in fields:
                rv = getattr(row, f, None)
                if rv is None or abs(rv - target[f]) > _TOL * max(abs(target[f]), 1e-9):
                    ok = False
                    break
            if ok:
                return row
        return None

    @staticmethod
    def _upsert(Model, catalog, brand, product, dry_run, review_notes=None):
        existing, matched_by = ScraperService._find_existing(Model, catalog, product)

        if matched_by == 'name_other_catalog':
            return {'result': 'blocked',
                    'detail': {'id': product.external_id, 'reason': 'nombre colisiona con otra marca'}}
        if existing and existing.is_locked:
            return {'result': 'skipped', 'detail': {'id': product.external_id, 'reason': 'bloqueado (edición manual)'}}

        if dry_run:
            return {'result': 'updated' if existing else 'created',
                    'detail': {'id': product.external_id, 'nombre': product.fields.get('nombre'),
                               'matched_by': matched_by, 'needs_review': bool(review_notes)}}

        row = existing or Model(catalog_id=catalog.id)
        skip_keys = {'nombre'} if matched_by == 'vitals' else set()
        for key, value in product.fields.items():
            if key in skip_keys:
                continue
            if hasattr(row, key):
                setattr(row, key, value)
        row.catalog_id = catalog.id
        row.source = f'scraper:{brand.lower()}'
        row.source_url = product.source_url
        if matched_by != 'vitals':
            row.external_id = product.external_id
        row.scraped_at = datetime.utcnow()
        row.needs_review = bool(review_notes)
        row.review_notes = review_notes
        if existing is None:
            db.session.add(row)
        db.session.commit()
        return {'result': 'updated' if existing else 'created',
                'detail': {'id': product.external_id, 'nombre': row.nombre,
                           'matched_by': matched_by, 'needs_review': bool(review_notes)}}

    @staticmethod
    def _record_run(brand, dry_run, report):
        if dry_run:
            return
        run = ScrapeRun(
            brand=brand, status='ok', dry_run=dry_run,
            created_count=len(report['created']), updated_count=len(report['updated']),
            skipped_count=len(report['skipped']) + len(report['blocked']),
            error_count=len(report['errors']),
            started_at=datetime.utcnow(), finished_at=datetime.utcnow(),
        )
        db.session.add(run)
        db.session.commit()
```

- [ ] **Step 4: Run, expect PASS** — `python -m pytest tests/test_autosolar_scraper.py::RoutingTest -v`

- [ ] **Step 5: No-regresión Fronius** — `python -m pytest tests/test_batteries_integration.py -v`

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat(scraper): enrutado por producto + dedup por marca/vitales"`

---

### Task 6: `AutoSolarScraper` + registro

**Files:**
- Create: `app/scrapers/autosolar.py`
- Modify: `app/scrapers/registry.py`
- Create: `tests/fixtures/autosolar/inverter.html`, `tests/fixtures/autosolar/panel.html`
- Test: `tests/test_autosolar_scraper.py`

**Interfaces:**
- Consumes: `deduce_brand`, `grab`, `to_float_eu`, `power_from_name`, `NormalizedProduct`.
- Produces: `AutoSolarScraper` con `brand='AutoSolar'`, `requires_product_brand=True`, `discover/fetch/parse`. `parse(ref, raw)` usa `lxml` para extraer título, atributo de fabricante y specs.

- [ ] **Step 1: Create fixtures** — HTML mínimos que reflejan la estructura de ficha (título + bloque de marca + tabla de specs). `inverter.html`:

```html
<html><head><meta itemprop="brand" content="Huawei"></head>
<body><h1 class="product-name">Inversor Huawei SUN2000 5KTL 5kW</h1>
<table class="data-sheet">
<tr><td>Potencia nominal</td><td>5 kW</td></tr>
<tr><td>Tensión máxima de entrada</td><td>1100 V</td></tr>
<tr><td>Rendimiento máximo</td><td>98,4 %</td></tr>
</table></body></html>
```

`panel.html`:

```html
<html><head><meta itemprop="brand" content="JA Solar"></head>
<body><h1 class="product-name">Panel JA Solar JAM72S30 545W</h1>
<table class="data-sheet">
<tr><td>Potencia</td><td>545 W</td></tr>
<tr><td>Tensión de circuito abierto (Voc)</td><td>49,7 V</td></tr>
<tr><td>Tensión de máxima potencia (Vmp)</td><td>41,8 V</td></tr>
<tr><td>Corriente de máxima potencia (Imp)</td><td>13,04 A</td></tr>
</table></body></html>
```

- [ ] **Step 2: Failing test**

```python
import os
from app.scrapers.autosolar import AutoSolarScraper

FIX = os.path.join(os.path.dirname(__file__), 'fixtures', 'autosolar')

class AutoSolarParseTest(unittest.TestCase):
    def _raw(self, name):
        with open(os.path.join(FIX, name), encoding='utf-8') as fh:
            return fh.read()

    def test_parse_inverter(self):
        s = AutoSolarScraper()
        ref = {'external_id': 'inv1', 'url': 'http://a/inv1', 'kind': 'inverter'}
        [p] = s.parse(ref, self._raw('inverter.html'))
        self.assertEqual(p.kind, 'inverter')
        self.assertEqual(p.brand, 'Huawei')
        self.assertEqual(p.fields['power'], 5)
        self.assertEqual(p.fields['vmax'], 1100)
        self.assertAlmostEqual(p.fields['y'], 98.4)

    def test_parse_panel(self):
        s = AutoSolarScraper()
        ref = {'external_id': 'pan1', 'url': 'http://a/pan1', 'kind': 'panel'}
        [p] = s.parse(ref, self._raw('panel.html'))
        self.assertEqual(p.brand, 'JA Solar')
        self.assertEqual(p.fields['power'], 545)
        self.assertAlmostEqual(p.fields['voc'], 49.7)
        self.assertAlmostEqual(p.fields['vmp'], 41.8)
        self.assertAlmostEqual(p.fields['imp'], 13.04)
```

- [ ] **Step 3: Run, expect FAIL**

- [ ] **Step 4: Implement `app/scrapers/autosolar.py`**

```python
"""Adapter de Autosolar (distribuidor multi-marca).

Autosolar vende equipos de muchos fabricantes; cada ficha declara la marca (atributo
estructurado) y una tabla de especificaciones. La identidad y la marca salen de la
página; el servicio enruta cada producto al catálogo de su marca. Sin marca deducida,
el producto no entra (requires_product_brand).
"""

import logging
import lxml.html
import requests

from .base import NormalizedProduct, to_float_eu, power_from_name
from .brands import deduce_brand

logger = logging.getLogger(__name__)

_UA = 'SunalyzeBot/0.1 (+catalog-sync; contact: ops@sunalyze.es)'

SEED = [
    {'kind': 'inverter', 'url': 'https://autosolar.es/inversores'},
    {'kind': 'panel', 'url': 'https://autosolar.es/placas-solares'},
]


def _cell(doc, labels, unit):
    for row in doc.cssselect('table.data-sheet tr'):
        cells = row.cssselect('td')
        if len(cells) < 2:
            continue
        label = cells[0].text_content().lower()
        if any(l.lower() in label for l in labels):
            import re
            m = re.search(r'([0-9][0-9.,]*)\s*' + unit, cells[1].text_content())
            if m:
                return to_float_eu(m.group(1))
    return None


class AutoSolarScraper:
    brand = 'AutoSolar'
    requires_product_brand = True

    def discover(self):
        return []

    def fetch(self, ref):
        resp = requests.get(ref['url'], headers={'User-Agent': _UA}, timeout=20)
        resp.raise_for_status()
        return resp.text

    def parse(self, ref, raw):
        doc = lxml.html.fromstring(raw)
        title_nodes = doc.cssselect('h1.product-name') or doc.cssselect('h1')
        title = title_nodes[0].text_content().strip() if title_nodes else ''
        attr_nodes = doc.cssselect('[itemprop="brand"]')
        attr = attr_nodes[0].get('content') if attr_nodes else None
        display, _ = deduce_brand(attr, title)

        kind = ref['kind']
        if kind == 'inverter':
            fields = {
                'nombre': title,
                'power': _cell(doc, ['potencia nominal', 'potencia de salida'], r'kW') or power_from_name(title),
                'vmax': _cell(doc, ['tensión máxima de entrada', 'tension maxima de entrada'], r'V'),
                'y': _cell(doc, ['rendimiento máximo', 'rendimiento maximo', 'eficiencia'], r'%'),
            }
        else:
            fields = {
                'nombre': title,
                'power': _cell(doc, ['potencia'], r'W'),
                'voc': _cell(doc, ['circuito abierto', 'voc'], r'V'),
                'vmp': _cell(doc, ['máxima potencia', 'maxima potencia', 'vmp'], r'V'),
                'imp': _cell(doc, ['corriente de máxima', 'corriente de maxima', 'imp'], r'A'),
            }
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=kind, external_id=ref['external_id'],
                                  source_url=ref['url'], fields=fields, brand=display)]
```

- [ ] **Step 5: Register** — en `registry.py` añadir import y entrada:

```python
from .autosolar import AutoSolarScraper
SCRAPERS = {
    'fronius': FroniusScraper(),
    'autosolar': AutoSolarScraper(),
}
```

- [ ] **Step 6: Run, expect PASS** — `python -m pytest tests/test_autosolar_scraper.py -v`

- [ ] **Step 7: Commit** — `git add -A && git commit -m "feat(scraper): adapter Autosolar + registro"`

---

### Task 7: Panel superadmin — listar/CRUD/activar catálogos

**Files:**
- Create: `app/superadmin/catalog_admin.py`
- Modify: `app/superadmin/views.py`, `app/superadmin/templates/superadmin/base.html`
- Create: `app/superadmin/templates/superadmin/catalogs.html`, `catalog_detail.html`
- Test: `tests/test_catalog_admin.py`

**Interfaces:**
- Produces: rutas `GET /catalogs`, `GET /catalogs/<id>`, `POST /catalogs`, `POST /catalogs/<id>/edit`, `POST /catalogs/<id>/activate`, `POST /catalogs/<id>/deactivate`, `POST /catalogs/<id>/delete`. `catalog_admin.list_all()`, `set_active(id, value)`, `counts(catalog)`.

- [ ] **Step 1: Failing test** (usa login de superadmin vía sesión + flag)

```python
class CatalogAdminTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        from app.models.user import User
        self.su = User(email='su@x.com', first_name='S', last_name='U', email_verified=True, is_superadmin=True)
        self.su.set_password('x'); db.session.add(self.su); db.session.commit()
        from app.services.catalog_service import CatalogService
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
        c = self._client()
        r = c.post(f'/superadmin/catalogs/{self.cat.id}/activate', data={'csrf_token': 'x'})
        self.assertEqual(r.status_code, 302)
        from app.models.catalog import Catalog
        self.assertTrue(Catalog.query.get(self.cat.id).is_active)
```

> Nota: el blueprint superadmin se monta con prefijo `/superadmin` (confirmar en `create_app`/registro del blueprint y ajustar las rutas del test). Si el IP allowlist bloquea en tests, `SUPERADMIN_IP_ALLOWLIST` vacío lo desactiva (`ip_allowed()` devuelve True sin allowlist).

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement `app/superadmin/catalog_admin.py`**

```python
"""Operaciones de superadmin sobre catálogos: listado completo, CRUD y activación.

A diferencia de CatalogService (que filtra por visibilidad de usuario), aquí se ven
TODOS los catálogos, incluidos los inactivos en cuarentena.
"""

from app.extensions import db
from app.models.catalog import Catalog
from app.services.catalog_service import CatalogService


def list_all():
    rows = Catalog.query.filter(Catalog.deleted_at.is_(None)).order_by(
        Catalog.is_active, Catalog.nombre).all()
    return [{**c.to_dict(), 'counts': CatalogService._counts(c.id)} for c in rows]


def get(catalog_id):
    return Catalog.query.filter(Catalog.id == catalog_id, Catalog.deleted_at.is_(None)).first()


def set_active(catalog_id, value):
    catalog = get(catalog_id)
    if not catalog:
        return None
    catalog.is_active = value
    db.session.commit()
    return catalog


def create(nombre, descripcion, scraper_name, is_official):
    catalog = Catalog(nombre=nombre.strip(), descripcion=(descripcion or '').strip(),
                      scraper_name=(scraper_name or '').strip() or None,
                      org_id=None, is_official=is_official, is_active=True)
    db.session.add(catalog)
    db.session.commit()
    return catalog


def edit(catalog_id, nombre, descripcion, scraper_name):
    catalog = get(catalog_id)
    if not catalog:
        return None
    catalog.nombre = nombre.strip()
    catalog.descripcion = (descripcion or '').strip()
    catalog.scraper_name = (scraper_name or '').strip() or None
    db.session.commit()
    return catalog


def delete(catalog_id):
    catalog = get(catalog_id)
    if catalog:
        catalog.soft_delete()
        db.session.commit()
    return catalog
```

- [ ] **Step 4: Add routes to `views.py`** (importar `catalog_admin` y `from app.superadmin.catalog_admin import ...` o `from app.superadmin import catalog_admin`):

```python
@superadmin_bp.route('/catalogs')
@require_superadmin
def catalogs_view():
    return render_template('superadmin/catalogs.html', catalogs=catalog_admin.list_all())


@superadmin_bp.route('/catalogs/<int:catalog_id>')
@require_superadmin
def catalog_detail(catalog_id):
    catalog = catalog_admin.get(catalog_id)
    if not catalog:
        abort(404)
    others = [c for c in catalog_admin.list_all() if c['id'] != catalog_id and c['is_active']]
    return render_template('superadmin/catalog_detail.html', c=catalog,
                           counts=CatalogService._counts(catalog_id), targets=others)


@superadmin_bp.route('/catalogs', methods=['POST'])
@require_superadmin
def catalog_create():
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio.', 'error')
        return redirect(url_for('superadmin.catalogs_view'))
    c = catalog_admin.create(nombre, request.form.get('descripcion'),
                             request.form.get('scraper_name'),
                             request.form.get('is_official') == 'on')
    log_action('catalog.create', target=f'catalog:{c.id}', detail=c.nombre)
    flash(f'Catálogo «{c.nombre}» creado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/edit', methods=['POST'])
@require_superadmin
def catalog_edit(catalog_id):
    c = catalog_admin.edit(catalog_id, request.form.get('nombre') or '',
                           request.form.get('descripcion'), request.form.get('scraper_name'))
    if not c:
        abort(404)
    log_action('catalog.edit', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash('Catálogo actualizado.', 'ok')
    return redirect(url_for('superadmin.catalog_detail', catalog_id=catalog_id))


@superadmin_bp.route('/catalogs/<int:catalog_id>/activate', methods=['POST'])
@require_superadmin
def catalog_activate(catalog_id):
    c = catalog_admin.set_active(catalog_id, True)
    if not c:
        abort(404)
    log_action('catalog.activate', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» activado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/deactivate', methods=['POST'])
@require_superadmin
def catalog_deactivate(catalog_id):
    c = catalog_admin.set_active(catalog_id, False)
    if not c:
        abort(404)
    log_action('catalog.deactivate', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» desactivado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/delete', methods=['POST'])
@require_superadmin
def catalog_delete(catalog_id):
    c = catalog_admin.delete(catalog_id)
    if not c:
        abort(404)
    log_action('catalog.delete', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» eliminado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))
```

Importar `CatalogService` y `catalog_admin` arriba en `views.py`:

```python
from app.services.catalog_service import CatalogService
from app.superadmin import catalog_admin
```

- [ ] **Step 5: Nav** — en `base.html`, tras la línea de "Equipos":

```html
      <a href="{{ url_for('superadmin.catalogs_view') }}" class="{{ 'active' if active_nav=='catalogs' }}">Catálogos</a>
```

- [ ] **Step 6: Templates** — `catalogs.html`:

```html
{% extends 'superadmin/base.html' %}
{% set active_nav = 'catalogs' %}
{% block body %}
<h1>Catálogos</h1>
<table>
  <tr><th>Nombre</th><th>scraper_name</th><th>Estado</th><th>Equipos</th><th></th></tr>
  {% for c in catalogs %}
  <tr>
    <td><a href="{{ url_for('superadmin.catalog_detail', catalog_id=c.id) }}">{{ c.nombre }}</a></td>
    <td class="muted">{{ c.scraper_name or '—' }}</td>
    <td>{% if c.is_active %}<span class="tag ok">activo</span>{% else %}<span class="tag warn">inactivo</span>{% endif %}</td>
    <td class="muted">{{ c.counts.panels }}p / {{ c.counts.inverters }}i</td>
    <td>
      {% if c.is_active %}
      <form class="inline" method="post" action="{{ url_for('superadmin.catalog_deactivate', catalog_id=c.id) }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button>Desactivar</button></form>
      {% else %}
      <form class="inline" method="post" action="{{ url_for('superadmin.catalog_activate', catalog_id=c.id) }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="primary">Activar</button></form>
      {% endif %}
    </td>
  </tr>
  {% else %}<tr><td colspan="5" class="muted">Sin catálogos.</td></tr>{% endfor %}
</table>
<h2>Crear catálogo</h2>
<form method="post" action="{{ url_for('superadmin.catalog_create') }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <label>Nombre</label><input type="text" name="nombre">
  <label>scraper_name</label><input type="text" name="scraper_name">
  <label>Descripción</label><input type="text" name="descripcion">
  <label><input type="checkbox" name="is_official"> Oficial</label>
  <p><button class="primary">Crear</button></p>
</form>
{% endblock %}
```

`catalog_detail.html`:

```html
{% extends 'superadmin/base.html' %}
{% set active_nav = 'catalogs' %}
{% block body %}
<h1>{{ c.nombre }} {% if not c.is_active %}<span class="tag warn">inactivo</span>{% endif %}</h1>
<p class="muted">scraper_name: {{ c.scraper_name or '—' }} · {{ counts.panels }} paneles · {{ counts.inverters }} inversores</p>
<h2>Editar</h2>
<form method="post" action="{{ url_for('superadmin.catalog_edit', catalog_id=c.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <label>Nombre</label><input type="text" name="nombre" value="{{ c.nombre }}">
  <label>scraper_name</label><input type="text" name="scraper_name" value="{{ c.scraper_name or '' }}">
  <label>Descripción</label><input type="text" name="descripcion" value="{{ c.descripcion }}">
  <p><button class="primary">Guardar</button></p>
</form>
<h2>Merge en otro catálogo</h2>
<form method="get" action="{{ url_for('superadmin.catalog_merge_preview', catalog_id=c.id) }}">
  <label>Destino</label>
  <select name="target">
    {% for t in targets %}<option value="{{ t.id }}">{{ t.nombre }}</option>{% endfor %}
  </select>
  <p><button>Previsualizar merge</button></p>
</form>
{% endblock %}
```

- [ ] **Step 7: Run, expect PASS** — `python -m pytest tests/test_catalog_admin.py::CatalogAdminTest -v`

- [ ] **Step 8: Commit** — `git add -A && git commit -m "feat(superadmin): gestión de catálogos (CRUD + activar)"`

---

### Task 8: Merge de catálogos con resolución 1 a 1

**Files:**
- Modify: `app/superadmin/catalog_admin.py`
- Modify: `app/superadmin/views.py`
- Create: `app/superadmin/templates/superadmin/catalog_merge.html`
- Test: `tests/test_catalog_admin.py`

**Interfaces:**
- Consumes: `set_active`, `ScraperService._match_by_vitals`-style comparación (reusar `_norm_name` y tolerancia local).
- Produces:
  - `catalog_admin.merge_preview(src_id, target_id) -> {'src','target','moves':[item], 'conflicts':[{'src':item,'target':item}]}`.
  - `catalog_admin.merge_apply(src_id, target_id, decisions: dict[str,str]) -> {'moved','dropped','replaced'}` (decisión por `f'{kind}:{src_item_id}'` ∈ `keep_a`/`use_b`).
  - Rutas `GET /catalogs/<id>/merge`, `POST /catalogs/<id>/merge`.

- [ ] **Step 1: Failing test**

```python
class CatalogMergeTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app(); self.ctx = self.app.app_context(); self.ctx.push(); db.create_all()
        from app.services.catalog_service import CatalogService
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
        from app.models.catalog import Catalog
        prev = catalog_admin.merge_preview(self.B.id, self.A.id)
        conflict_key = f"panel:{prev['conflicts'][0]['src']['id']}"
        res = catalog_admin.merge_apply(self.B.id, self.A.id, {conflict_key: 'keep_a'})
        self.assertEqual(res['moved'], 1)
        self.assertEqual(res['dropped'], 1)
        self.assertEqual(Panel.query.filter_by(catalog_id=self.A.id).count(), 2)
        self.assertTrue(Catalog.query.get(self.B.id).is_deleted)
```

- [ ] **Step 2: Run, expect FAIL**

- [ ] **Step 3: Implement merge en `catalog_admin.py`**

```python
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.wire import Wire
from app.models.catalog import CatalogSubscription

_MERGE_MODELS = {'panel': Panel, 'inverter': Inverter, 'battery': Battery, 'wire': Wire}
_VITAL_NUM = {'panel': ('power', 'voc', 'vmp', 'imp'), 'inverter': ('power', 'vmax')}
_TOL = 0.02


def _norm(name):
    return ' '.join((name or '').lower().split())


def _semantic_match(item, kind, target_rows):
    n = _norm(item.nombre)
    for row in target_rows:
        if _norm(row.nombre) == n:
            return row
    fields = _VITAL_NUM.get(kind)
    if not fields:
        return None
    vals = {f: getattr(item, f, None) for f in fields}
    if any(vals[f] is None for f in fields):
        return None
    for row in target_rows:
        if all(getattr(row, f, None) is not None and
               abs(getattr(row, f) - vals[f]) <= _TOL * max(abs(vals[f]), 1e-9) for f in fields):
            return row
    return None


def merge_preview(src_id, target_id):
    src, target = get(src_id), get(target_id)
    moves, conflicts = [], []
    for kind, Model in _MERGE_MODELS.items():
        target_rows = Model.query.filter_by(catalog_id=target_id).all()
        for item in Model.query.filter_by(catalog_id=src_id).all():
            match = _semantic_match(item, kind, target_rows)
            if match:
                conflicts.append({'kind': kind, 'src': item.to_dict(), 'target': match.to_dict()})
            else:
                moves.append({'kind': kind, 'src': item.to_dict()})
    return {'src': src.to_dict() if src else None,
            'target': target.to_dict() if target else None,
            'moves': moves, 'conflicts': conflicts}


def merge_apply(src_id, target_id, decisions):
    moved = dropped = replaced = 0
    for kind, Model in _MERGE_MODELS.items():
        target_rows = Model.query.filter_by(catalog_id=target_id).all()
        for item in Model.query.filter_by(catalog_id=src_id).all():
            match = _semantic_match(item, kind, target_rows)
            if not match:
                item.catalog_id = target_id
                moved += 1
                continue
            decision = decisions.get(f'{kind}:{item.id}', 'keep_a')
            if decision == 'use_b' and not getattr(match, 'is_locked', False):
                db.session.delete(match)
                db.session.flush()
                item.catalog_id = target_id
                replaced += 1
            else:
                db.session.delete(item)
                dropped += 1
    for sub in CatalogSubscription.query.filter_by(catalog_id=src_id).all():
        dup = CatalogSubscription.query.filter_by(org_id=sub.org_id, catalog_id=target_id).first()
        if dup:
            db.session.delete(sub)
        else:
            sub.catalog_id = target_id
    src = get(src_id)
    if src:
        src.soft_delete()
    db.session.commit()
    return {'moved': moved, 'dropped': dropped, 'replaced': replaced}
```

- [ ] **Step 4: Routes en `views.py`**

```python
@superadmin_bp.route('/catalogs/<int:catalog_id>/merge')
@require_superadmin
def catalog_merge_preview(catalog_id):
    target_id = request.args.get('target', type=int)
    if not target_id:
        flash('Selecciona un catálogo destino.', 'error')
        return redirect(url_for('superadmin.catalog_detail', catalog_id=catalog_id))
    preview = catalog_admin.merge_preview(catalog_id, target_id)
    return render_template('superadmin/catalog_merge.html', preview=preview,
                           src_id=catalog_id, target_id=target_id)


@superadmin_bp.route('/catalogs/<int:catalog_id>/merge', methods=['POST'])
@require_superadmin
def catalog_merge_apply(catalog_id):
    target_id = request.form.get('target', type=int)
    decisions = {k[len('decision:'):]: v for k, v in request.form.items() if k.startswith('decision:')}
    res = catalog_admin.merge_apply(catalog_id, target_id, decisions)
    log_action('catalog.merge', target=f'catalog:{catalog_id}->{target_id}', detail=str(res))
    flash(f"Merge: {res['moved']} movidos, {res['dropped']} descartados, {res['replaced']} reemplazados.", 'ok')
    return redirect(url_for('superadmin.catalog_detail', catalog_id=target_id))
```

- [ ] **Step 5: Template `catalog_merge.html`**

```html
{% extends 'superadmin/base.html' %}
{% set active_nav = 'catalogs' %}
{% block body %}
<h1>Merge: {{ preview.src.nombre }} → {{ preview.target.nombre }}</h1>
<form method="post" action="{{ url_for('superadmin.catalog_merge_apply', catalog_id=src_id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <input type="hidden" name="target" value="{{ target_id }}">
  <h2>Se moverán ({{ preview.moves|length }})</h2>
  <ul>{% for m in preview.moves %}<li class="muted">{{ m.kind }}: {{ m.src.nombre }}</li>{% else %}<li class="muted">Nada.</li>{% endfor %}</ul>
  <h2>Conflictos ({{ preview.conflicts|length }})</h2>
  <table>
    <tr><th>Origen (B)</th><th>Destino (A)</th><th>Decisión</th></tr>
    {% for cf in preview.conflicts %}
    <tr>
      <td>{{ cf.src.nombre }}</td><td>{{ cf.target.nombre }}</td>
      <td>
        <select name="decision:{{ cf.kind }}:{{ cf.src.id }}">
          <option value="keep_a">Conservar A</option>
          <option value="use_b">Usar B</option>
        </select>
      </td>
    </tr>
    {% else %}<tr><td colspan="3" class="muted">Sin conflictos.</td></tr>{% endfor %}
  </table>
  <p><button class="primary">Ejecutar merge</button></p>
</form>
{% endblock %}
```

- [ ] **Step 6: Run, expect PASS** — `python -m pytest tests/test_catalog_admin.py::CatalogMergeTest -v`

- [ ] **Step 7: Full suite** — `python -m pytest tests/ -v`

- [ ] **Step 8: Commit** — `git add -A && git commit -m "feat(superadmin): merge de catálogos con resolución 1 a 1"`

---

## Self-Review

- **Spec coverage:** §3 (modelo+migración)→T1; §4.2 (brands)→T2; §4.1 (brand field)→T3; §6+§7 (visibilidad+official_catalog)→T4; §5 (enrutado+dedup, supervivencia de nombre)→T5; §4.3/4.4 (scraper+registro)→T6; §8 (CRUD+activar)→T7; §8.1 (merge 1 a 1)→T8. Cubierto.
- **Placeholders:** ninguno; todo el código es concreto. Las URLs de `SEED`/`discover()` de Autosolar quedan como esqueleto (`discover` devuelve `[]`) a propósito: el parseo real está testeado con fixtures; el crawling de listados se afina contra el sitio real en ejecución (riesgo documentado en el spec).
- **Type consistency:** `matched_by` ∈ {external_id,name,name_other_catalog,vitals}; `merge_apply` claves `f'{kind}:{id}'`; `decision` ∈ {keep_a,use_b}. Consistentes entre tareas.

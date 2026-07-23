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
from app.models.wire import Wire
from app.models.scrape_run import ScrapeRun
from app.services.catalog_service import CatalogService
from app.scrapers.registry import get_scraper
from app.scrapers import acceptance

logger = logging.getLogger(__name__)

_MODEL = {'panel': Panel, 'inverter': Inverter, 'wire': Wire}
_VITAL_NUM = {'panel': ('power', 'voc', 'vmp', 'imp'), 'inverter': ('power', 'vmax'),
              'wire': ('seccion', 'corriente')}
_TOL = 0.02


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
                    report['blocked'].append({'id': product.external_id,
                                              'reason': f'tipo no soportado: {product.kind}'})
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
            return {'result': 'skipped',
                    'detail': {'id': product.external_id, 'reason': 'bloqueado (edición manual)'}}

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

"""Orquestación del scraping: discover → fetch → parse → upsert con provenance.

Reglas:
- Solo se persisten productos con sus campos VITALES; los parciales (sin campos
  no-vitales) se guardan igual, con esos campos a null.
- Upsert por (catálogo de la marca, external_id); si el equipo está `is_locked`
  (editado a mano) NO se pisa.
- dry_run no escribe: reporta qué haría.
- Cada corrida queda registrada en `ScrapeRun`.
"""

import logging
from datetime import datetime

from app.extensions import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.catalog import Catalog
from app.models.scrape_run import ScrapeRun
from app.scrapers.registry import get_scraper
from app.scrapers import acceptance

logger = logging.getLogger(__name__)

_MODEL = {'panel': Panel, 'inverter': Inverter}


def _official_catalog(brand):
    catalog = Catalog.query.filter_by(nombre=brand, org_id=None).first()
    if not catalog:
        catalog = Catalog(nombre=brand, descripcion=f'Catálogo oficial de {brand}',
                          org_id=None, is_official=True)
        db.session.add(catalog)
        db.session.flush()
    return catalog


class ScraperService:

    @staticmethod
    def run(brand, dry_run=False):
        scraper = get_scraper(brand)
        if not scraper:
            raise ValueError(f'No hay scraper registrado para «{brand}».')

        report = {'brand': scraper.brand, 'dry_run': dry_run,
                  'created': [], 'updated': [], 'review': [], 'blocked': [],
                  'skipped': [], 'errors': []}

        catalog = _official_catalog(scraper.brand)
        Model = _MODEL[scraper.kind]

        for ref in scraper.discover():
            try:
                raw = scraper.fetch(ref)
                products = scraper.parse(ref, raw)
            except Exception as exc:
                logger.exception('Fallo al obtener %s', ref.get('url'))
                report['errors'].append({'ref': ref.get('external_id'), 'error': str(exc)})
                continue

            for product in products:
                verdict = acceptance.evaluate(product, scraper.brand)
                if verdict['verdict'] == 'blocked':
                    report['blocked'].append({'id': product.external_id,
                                              'reason': '; '.join(verdict['block'])})
                    continue
                review_notes = '; '.join(verdict['review']) if verdict['verdict'] == 'review' else None
                action = ScraperService._upsert(Model, catalog, scraper.brand, product,
                                                dry_run, review_notes)
                report[action['result']].append(action['detail'])
                if review_notes:
                    report['review'].append({'id': product.external_id, 'reason': review_notes})

        ScraperService._record_run(scraper.brand, dry_run, report)
        return report

    @staticmethod
    def _upsert(Model, catalog, brand, product, dry_run, review_notes=None):
        existing = Model.query.filter_by(catalog_id=catalog.id, external_id=product.external_id).first()
        if not existing:
            existing = Model.query.filter_by(nombre=product.fields.get('nombre')).first()

        if existing and existing.is_locked:
            return {'result': 'skipped', 'detail': {'id': product.external_id, 'reason': 'bloqueado (edición manual)'}}

        partial = sorted(set(['y', 'power_max', 'I_max_input', 'I_max_output',
                              'tcp', 'tcv', 'isc', 't_noct', 'height', 'width'])
                         - set(product.fields.keys()))

        if dry_run:
            result = 'updated' if existing else 'created'
            return {'result': result, 'detail': {'id': product.external_id,
                    'nombre': product.fields.get('nombre'), 'parcial_sin': partial,
                    'needs_review': bool(review_notes)}}

        row = existing or Model(catalog_id=catalog.id)
        for key, value in product.fields.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.catalog_id = catalog.id
        row.source = f'scraper:{brand.lower()}'
        row.source_url = product.source_url
        row.external_id = product.external_id
        row.scraped_at = datetime.utcnow()
        row.needs_review = bool(review_notes)
        row.review_notes = review_notes
        if existing is None:
            db.session.add(row)
        db.session.commit()
        return {'result': 'updated' if existing else 'created',
                'detail': {'id': product.external_id, 'nombre': row.nombre, 'parcial_sin': partial,
                           'needs_review': bool(review_notes)}}

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

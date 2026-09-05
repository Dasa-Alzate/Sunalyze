
import logging
import re
from datetime import datetime

from app.extensions import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.wire import Wire
from app.models.scrape_run import ScrapeRun
from app.services.catalog_service import CatalogService
from app.scrapers.registry import get_scraper
from app.scrapers import acceptance

logger = logging.getLogger(__name__)

_MODEL = {'panel': Panel, 'inverter': Inverter, 'battery': Battery, 'wire': Wire}
_VITAL_NUM = {'panel': ('power', 'voc', 'vmp', 'imp'), 'inverter': ('power', 'vmax'),
              'battery': ('capacity_kwh', 'power_kw', 'voltage'),
              'wire': ('seccion', 'corriente')}
_TOL = 0.005
_BATCH = 100

_PRIORITY = {'scraper:fronius': 30, 'scraper:cec': 20, 'scraper:cec-baterias': 20,
             'scraper:cec-inversores': 20}
_BUNDLE = re.compile(r'\b(pack|pallet|palet|rollo|lote|kit|conjunto|unidades)\b',
                     re.IGNORECASE)
_DEFAULT_SCRAPER_PRIORITY = 10


_MISSING_FIELD = re.compile(r'falta campo requerido:\s*([a-zA-Z_]+)')


def _surviving_reasons(row, review_notes):
    if not review_notes:
        return None
    kept = []
    for reason in review_notes.split('; '):
        match = _MISSING_FIELD.search(reason)
        if match and getattr(row, match.group(1), None) not in (None, ''):
            continue
        kept.append(reason)
    return '; '.join(kept) or None


def _priority(source):
    if not source or not source.startswith('scraper:'):
        return 0
    return _PRIORITY.get(source, _DEFAULT_SCRAPER_PRIORITY)


class ScraperService:

    @staticmethod
    def run(brand, dry_run=False, limit=None, force=False):
        scraper = get_scraper(brand)
        if not scraper:
            raise ValueError(f'No hay scraper registrado para «{brand}».')
        source_key = brand.lower()
        scraper._force = force
        run_started = datetime.utcnow()

        report = {'brand': scraper.brand, 'dry_run': dry_run,
                  'created': [], 'updated': [], 'review': [], 'blocked': [],
                  'skipped': [], 'errors': [], 'unchanged': 0, 'discovered': 0}
        catalog_cache = {}
        pending = 0
        processed = 0

        refs = scraper.discover()
        report['discovered'] = len(refs)

        for ref in refs:
            if limit and processed >= limit:
                break
            try:
                raw = scraper.fetch(ref, force=force)
            except Exception as exc:
                logger.exception('Fallo al obtener %s', ref.get('url'))
                report['errors'].append({'ref': ref.get('external_id'), 'error': str(exc)})
                continue

            if raw is None:
                report['unchanged'] += 1
                processed += 1
                continue

            try:
                products = scraper.parse(ref, raw)
            except Exception as exc:
                logger.exception('Fallo al parsear %s', ref.get('url'))
                report['errors'].append({'ref': ref.get('external_id'), 'error': str(exc)})
                continue

            processed += 1
            stored = False
            for product in products:
                outcome = ScraperService._ingest(product, scraper, catalog_cache,
                                                 dry_run, report, source_key, run_started)
                stored = stored or outcome

            if stored and not dry_run:
                scraper.remember(ref)
                pending += 1
                if pending >= _BATCH:
                    pending = ScraperService._flush(report)

        if not dry_run and pending:
            ScraperService._flush(report)

        ScraperService._record_run(scraper.brand, dry_run, report)
        return report

    @staticmethod
    def _flush(report):
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.exception('Fallo al confirmar el lote')
            report['errors'].append({'ref': '(lote)', 'error': str(exc)})
        return 0

    @staticmethod
    def _ingest(product, scraper, catalog_cache, dry_run, report, source_key, run_started):
        catalog_brand = product.brand or (
            None if getattr(scraper, 'requires_product_brand', False) else scraper.brand)
        if not catalog_brand:
            report['blocked'].append({'id': product.external_id, 'reason': 'sin marca deducida'})
            return False
        if product.kind not in _MODEL:
            report['blocked'].append({'id': product.external_id,
                                      'reason': f'tipo no soportado: {product.kind}'})
            return False

        verdict = acceptance.evaluate(product, catalog_brand)
        if verdict['verdict'] == 'blocked':
            report['blocked'].append({'id': product.external_id, 'reason': '; '.join(verdict['block'])})
            return False

        reasons = list(verdict['review']) + list(product.notes or [])
        review_notes = '; '.join(reasons) if reasons else None

        if catalog_brand not in catalog_cache:
            catalog_cache[catalog_brand] = CatalogService.official_catalog(catalog_brand, active=False)
        catalog = catalog_cache[catalog_brand]

        try:
            action = ScraperService._upsert(_MODEL[product.kind], catalog, source_key,
                                           product, dry_run, review_notes, run_started)
        except Exception as exc:
            db.session.rollback()
            logger.exception('Fallo al guardar %s', product.external_id)
            report['errors'].append({'ref': product.external_id, 'error': str(exc)})
            return False

        report[action['result']].append(action['detail'])
        if review_notes and action['result'] != 'blocked':
            report['review'].append({'id': product.external_id, 'reason': review_notes})
        return action['result'] in ('created', 'updated')

    @staticmethod
    def _find_existing(Model, catalog, product, run_started=None):
        existing = Model.query.filter_by(catalog_id=catalog.id, external_id=product.external_id).first()
        if existing:
            return existing, 'external_id'
        nombre = product.fields.get('nombre')
        by_name = Model.query.filter_by(nombre=nombre).first() if nombre else None
        if by_name:
            return by_name, ('name' if by_name.catalog_id == catalog.id else 'name_other_catalog')
        match = ScraperService._match_by_vitals(Model, catalog, product, run_started)
        if match:
            return match, 'vitals'
        return None, None

    @staticmethod
    def _match_by_vitals(Model, catalog, product, run_started=None):
        fields = _VITAL_NUM[product.kind]
        target = {f: product.fields.get(f) for f in fields}
        if any(target[f] is None for f in fields):
            return None
        query = Model.query.filter(
            Model.catalog_id == catalog.id,
            Model.source.like('scraper:%'),
        )
        if run_started is not None:
            query = query.filter(db.or_(Model.scraped_at.is_(None),
                                        Model.scraped_at < run_started))
        for row in query.all():
            if _BUNDLE.search(getattr(row, 'nombre', '') or ''):
                continue
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
    def _upsert(Model, catalog, source_key, product, dry_run, review_notes=None, run_started=None):
        existing, matched_by = ScraperService._find_existing(Model, catalog, product, run_started)
        new_source = f'scraper:{source_key}'

        if matched_by == 'name_other_catalog':
            return {'result': 'blocked',
                    'detail': {'id': product.external_id, 'reason': 'nombre colisiona con otra marca'}}
        if existing and existing.is_locked:
            return {'result': 'skipped',
                    'detail': {'id': product.external_id, 'reason': 'bloqueado (edición manual)'}}

        if existing and _priority(existing.source) > _priority(new_source):
            return ScraperService._fill_gaps(existing, product, dry_run, matched_by)

        if dry_run:
            return {'result': 'updated' if existing else 'created',
                    'detail': {'id': product.external_id, 'nombre': product.fields.get('nombre'),
                               'matched_by': matched_by, 'needs_review': bool(review_notes)}}

        upgrades = existing is not None and _priority(new_source) > _priority(existing.source)
        row = existing or Model(catalog_id=catalog.id)
        skip_keys = {'nombre'} if matched_by == 'vitals' else set()
        for key, value in product.fields.items():
            if key in skip_keys:
                continue
            if hasattr(row, key):
                setattr(row, key, value)
        row.catalog_id = catalog.id
        row.source = new_source
        row.source_url = product.source_url
        if matched_by != 'vitals' or upgrades:
            row.external_id = product.external_id
        row.scraped_at = datetime.utcnow()
        surviving = _surviving_reasons(row, review_notes)
        row.needs_review = bool(surviving)
        row.review_notes = surviving[:500] if surviving else None
        if existing is None:
            db.session.add(row)
        db.session.flush()
        return {'result': 'updated' if existing else 'created',
                'detail': {'id': product.external_id, 'nombre': row.nombre,
                           'matched_by': matched_by, 'needs_review': bool(review_notes),
                           'source_upgraded': upgrades or None}}

    @staticmethod
    def _fill_gaps(row, product, dry_run, matched_by):
        fillable = {}
        for key, value in product.fields.items():
            if key == 'nombre' or not hasattr(row, key):
                continue
            if getattr(row, key) in (None, ''):
                fillable[key] = value
        if not fillable:
            return {'result': 'skipped',
                    'detail': {'id': product.external_id,
                               'reason': f'prevalece {row.source}; sin campos que aportar'}}
        if dry_run:
            return {'result': 'updated',
                    'detail': {'id': product.external_id, 'nombre': row.nombre,
                               'matched_by': matched_by, 'fill_only': sorted(fillable)}}
        for key, value in fillable.items():
            setattr(row, key, value)
        db.session.flush()
        return {'result': 'updated',
                'detail': {'id': product.external_id, 'nombre': row.nombre,
                           'matched_by': matched_by, 'fill_only': sorted(fillable)}}

    @staticmethod
    def _record_run(brand, dry_run, report):
        if dry_run:
            return
        run = ScrapeRun(
            brand=brand, status='ok', dry_run=dry_run,
            created_count=len(report['created']), updated_count=len(report['updated']),
            skipped_count=len(report['skipped']) + len(report['blocked']) + report['unchanged'],
            error_count=len(report['errors']),
            started_at=datetime.utcnow(), finished_at=datetime.utcnow(),
            notes=(f"descubiertos={report['discovered']} sin_cambios={report['unchanged']} "
                   f"a_revisar={len(report['review'])}"),
        )
        db.session.add(run)
        db.session.commit()

"""Operaciones de superadmin sobre catálogos: listado completo, CRUD, activación y merge.

A diferencia de CatalogService (que filtra por visibilidad de usuario), aquí se ven
TODOS los catálogos, incluidos los inactivos en cuarentena. El merge reasigna los
equipos del catálogo origen al destino; los duplicados semánticos (mismo equipo con
nombre distinto) se resuelven uno a uno según la decisión del superusuario.
"""

from app.extensions import db
from app.models.catalog import Catalog, CatalogSubscription
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.wire import Wire
from app.services.catalog_service import CatalogService

_MERGE_MODELS = {'panel': Panel, 'inverter': Inverter, 'battery': Battery, 'wire': Wire}
_VITAL_NUM = {'panel': ('power', 'voc', 'vmp', 'imp'), 'inverter': ('power', 'vmax')}
_TOL = 0.02


def list_all():
    rows = Catalog.query.filter(Catalog.deleted_at.is_(None)).order_by(
        Catalog.is_active, Catalog.nombre).all()
    counts = CatalogService.counts_map([c.id for c in rows])
    return [{**c.to_dict(), 'counts': counts[c.id]} for c in rows]


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

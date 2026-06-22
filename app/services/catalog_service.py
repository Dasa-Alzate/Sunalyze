"""Dominio de catalogos: biblioteca del workspace, marketplace y suscripciones.

Reglas de propiedad:
- Catalogo con org_id NULL -> marketplace (solo lectura; suscribible).
- Catalogo con org_id -> propiedad del workspace (CRUD por sus miembros).
- Biblioteca efectiva de un workspace = catalogos propios + suscritos.
"""

import logging

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.catalog import Catalog, CatalogSubscription
from app.errors import NotFound, Forbidden, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_CATALOG_NAME = 'Mis equipos'


class CatalogService:

    @staticmethod
    def own_catalog_ids(org_id):
        if not org_id:
            return []
        rows = db.session.query(Catalog.id).filter(Catalog.org_id == org_id).all()
        return [r[0] for r in rows]

    @staticmethod
    def subscribed_catalog_ids(org_id):
        if not org_id:
            return []
        rows = db.session.query(CatalogSubscription.catalog_id).filter(
            CatalogSubscription.org_id == org_id).all()
        return [r[0] for r in rows]

    @classmethod
    def visible_catalog_ids(cls, org_id):
        return sorted(set(cls.own_catalog_ids(org_id)) | set(cls.subscribed_catalog_ids(org_id)))

    @staticmethod
    def _counts(catalog_id):
        from app.models.panel import Panel
        from app.models.inverter import Inverter
        from app.models.battery import Battery
        from app.models.wire import Wire
        return {
            'panels': Panel.query.filter_by(catalog_id=catalog_id).count(),
            'inverters': Inverter.query.filter_by(catalog_id=catalog_id).count(),
            'batteries': Battery.query.filter_by(catalog_id=catalog_id).count(),
            'wires': Wire.query.filter_by(catalog_id=catalog_id).count(),
        }

    @classmethod
    def _serialize(cls, catalog, org_id, subscribed_ids):
        return {
            **catalog.to_dict(),
            'own': catalog.org_id == org_id,
            'subscribed': catalog.id in subscribed_ids,
            'counts': cls._counts(catalog.id),
        }

    @classmethod
    def library(cls, org_id):
        subscribed = set(cls.subscribed_catalog_ids(org_id))
        own = Catalog.query.filter(Catalog.org_id == org_id).order_by(Catalog.nombre).all()
        subs = Catalog.query.filter(Catalog.id.in_(subscribed)).order_by(Catalog.nombre).all() if subscribed else []
        return [cls._serialize(c, org_id, subscribed) for c in own + subs]

    @classmethod
    def marketplace(cls, org_id):
        subscribed = set(cls.subscribed_catalog_ids(org_id))
        public = Catalog.query.filter(Catalog.org_id.is_(None)).order_by(Catalog.nombre).all()
        return [cls._serialize(c, org_id, subscribed) for c in public]

    @staticmethod
    def create_catalog(org_id, nombre, descripcion=''):
        catalog = Catalog(nombre=nombre.strip(), descripcion=descripcion.strip(), org_id=org_id)
        db.session.add(catalog)
        db.session.commit()
        return catalog

    @staticmethod
    def delete_catalog(org_id, catalog_id):
        from app.models.panel import Panel
        from app.models.inverter import Inverter
        from app.models.battery import Battery
        from app.models.wire import Wire
        catalog = Catalog.query.get(catalog_id)
        if not catalog or catalog.org_id != org_id:
            raise NotFound('Catálogo no encontrado en tu workspace.')
        for model in (Panel, Inverter, Battery, Wire):
            model.query.filter_by(catalog_id=catalog.id).delete()
        CatalogSubscription.query.filter_by(catalog_id=catalog.id).delete()
        db.session.delete(catalog)
        db.session.commit()

    @staticmethod
    def ensure_default_catalog(org_id):
        catalog = Catalog.query.filter_by(org_id=org_id, nombre=DEFAULT_CATALOG_NAME).first()
        if not catalog:
            catalog = Catalog(
                nombre=DEFAULT_CATALOG_NAME,
                descripcion='Equipos propios del workspace',
                org_id=org_id,
            )
            db.session.add(catalog)
            db.session.flush()
        return catalog

    @staticmethod
    def resolve_target_catalog(org_id, catalog_id=None):
        if catalog_id:
            catalog = Catalog.query.get(catalog_id)
            if not catalog or catalog.org_id != org_id:
                raise NotFound('Catálogo no encontrado en tu workspace.')
            return catalog
        return CatalogService.ensure_default_catalog(org_id)

    @staticmethod
    def subscribe(org_id, catalog_id):
        catalog = Catalog.query.get(catalog_id)
        if not catalog or not catalog.is_marketplace:
            raise NotFound('Catálogo no disponible en el marketplace.')
        existing = CatalogSubscription.query.filter_by(org_id=org_id, catalog_id=catalog_id).first()
        if not existing:
            db.session.add(CatalogSubscription(org_id=org_id, catalog_id=catalog_id))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        return catalog

    @staticmethod
    def unsubscribe(org_id, catalog_id):
        CatalogSubscription.query.filter_by(org_id=org_id, catalog_id=catalog_id).delete()
        db.session.commit()

    @staticmethod
    def bootstrap_org(org_id):
        officials = Catalog.query.filter(Catalog.org_id.is_(None), Catalog.is_official.is_(True)).all()
        for catalog in officials:
            exists = CatalogSubscription.query.filter_by(org_id=org_id, catalog_id=catalog.id).first()
            if not exists:
                db.session.add(CatalogSubscription(org_id=org_id, catalog_id=catalog.id))
        db.session.commit()
        return len(officials)

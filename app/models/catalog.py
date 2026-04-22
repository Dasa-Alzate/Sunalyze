"""Catalogos de equipos: del marketplace (org_id NULL) o propios de un workspace."""

from app.extensions import db
from .database import BaseModel


class Catalog(BaseModel):
    """Coleccion de equipos.

    org_id NULL -> catalogo publico del marketplace (solo lectura para los
    usuarios; los oficiales se siembran con is_official=True).
    org_id presente -> catalogo privado del workspace, con CRUD completo.
    """
    __tablename__ = 'catalogs'

    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(255), default='')
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), index=True)
    is_official = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def is_marketplace(self):
        return self.org_id is None

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion or '',
            'org_id': self.org_id,
            'is_official': self.is_official,
            'is_marketplace': self.is_marketplace,
        }

    def __repr__(self):
        scope = 'marketplace' if self.is_marketplace else f'org {self.org_id}'
        return f'<Catalog {self.nombre} ({scope})>'


class CatalogSubscription(BaseModel):
    """Suscripcion de un workspace a un catalogo del marketplace."""
    __tablename__ = 'catalog_subscriptions'
    __table_args__ = (db.UniqueConstraint('org_id', 'catalog_id', name='uq_sub_org_catalog'),)

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id'), nullable=False, index=True)

    def __repr__(self):
        return f'<CatalogSubscription o{self.org_id} -> c{self.catalog_id}>'

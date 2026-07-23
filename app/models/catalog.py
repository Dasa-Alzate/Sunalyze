
from app.extensions import db
from .database import BaseModel, SoftDeleteMixin


class Catalog(BaseModel, SoftDeleteMixin):
    __tablename__ = 'catalogs'

    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(255), default='')
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True)
    is_official = db.Column(db.Boolean, nullable=False, default=False)
    scraper_name = db.Column(db.String(100), index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    color = db.Column(db.String(9))

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
            'scraper_name': self.scraper_name,
            'is_active': self.is_active,
            'color': self.color,
        }

    def __repr__(self):
        scope = 'marketplace' if self.is_marketplace else f'org {self.org_id}'
        return f'<Catalog {self.nombre} ({scope})>'


class CatalogSubscription(BaseModel):
    __tablename__ = 'catalog_subscriptions'
    __table_args__ = (db.UniqueConstraint('org_id', 'catalog_id', name='uq_sub_org_catalog'),)

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id', ondelete='CASCADE'), nullable=False, index=True)

    def __repr__(self):
        return f'<CatalogSubscription o{self.org_id} -> c{self.catalog_id}>'

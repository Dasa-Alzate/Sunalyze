"""Modelo de cable/conductor electrico."""

from app import db
from .database import BaseModel
from .provenance import ProvenanceMixin

class Wire(BaseModel, ProvenanceMixin):
    """
    Representa un cable electrico con sus especificaciones.

    Attributes:
        nombre: Nombre/modelo del cable (opcional; los cables suelen carecer de modelo propio).
        seccion: Seccion transversal del cable (mm2).
        corriente: Corriente maxima admisible (A).
        tipo: Tipo de cable (ej: 'B1', 'B2', 'F').
        material: Material conductor ('Cu' o 'Al').
        no_conductores: Numero de conductores.
    """
    __tablename__ = 'wires'

    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id'), index=True)
    catalog = db.relationship('Catalog')

    nombre = db.Column(db.String(100))
    seccion = db.Column(db.Float, nullable=False)
    corriente = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    material = db.Column(db.String(10), nullable=False)
    no_conductores = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'catalog_id': self.catalog_id,
            'catalog_nombre': self.catalog.nombre if self.catalog else None,
            'nombre': self.nombre,
            'seccion': self.seccion,
            'corriente': self.corriente,
            'tipo': self.tipo,
            'material': self.material,
            'no_conductores': self.no_conductores,
            **self.provenance_dict(),
        }

    def __repr__(self):
        return f'<Wire {self.tipo} {self.seccion}mm² {self.corriente}A>'

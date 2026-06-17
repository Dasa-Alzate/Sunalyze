"""Modelo de inversor fotovoltaico."""

from app import db
from .database import BaseModel
from .provenance import ProvenanceMixin

class Inverter(BaseModel, ProvenanceMixin):
    """
    Representa un inversor con sus especificaciones tecnicas.

    Attributes:
        nombre: Nombre/modelo del inversor.
        y: Eficiencia del inversor (%).
        power_max: Potencia maxima DC de entrada (kW).
        power: Potencia nominal AC de salida (kW).
        vmax: Voltaje maximo de entrada DC (V).
        I_max_input: Corriente maxima de entrada DC (A).
        I_max_output: Corriente maxima de salida AC (A).
    """
    __tablename__ = 'inverters'

    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id'), index=True)
    catalog = db.relationship('Catalog')

    nombre = db.Column(db.String(100), nullable=False, unique=True)
    power = db.Column(db.Float, nullable=False)
    vmax = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float)
    power_max = db.Column(db.Float)
    I_max_input = db.Column(db.Float)
    I_max_output = db.Column(db.Float)
    datasheet = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'catalog_id': self.catalog_id,
            'catalog_nombre': self.catalog.nombre if self.catalog else None,
            'nombre': self.nombre,
            'y': self.y,
            'power_max': self.power_max,
            'power': self.power,
            'vmax': self.vmax,
            'I_max_input': self.I_max_input,
            'I_max_output': self.I_max_output,
            'datasheet': self.datasheet,
            **self.provenance_dict(),
        }
    
    def __repr__(self):
        return f'<Inverter {self.nombre}>'
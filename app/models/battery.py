"""Modelo de bateria de almacenamiento fotovoltaico."""

from app import db
from .database import BaseModel
from .provenance import ProvenanceMixin

class Battery(BaseModel, ProvenanceMixin):
    """
    Representa una bateria de almacenamiento con sus especificaciones tecnicas.

    Attributes:
        nombre: Nombre/modelo de la bateria.
        capacity_kwh: Capacidad nominal (kWh).
        usable_kwh: Capacidad util (kWh).
        dod: Profundidad de descarga (%).
        power_kw: Potencia de carga/descarga (kW).
        voltage: Voltaje nominal (V).
        technology: Quimica/tecnologia (p. ej. LiFePO4).
        round_trip_efficiency: Eficiencia de ida y vuelta (%).
        max_cycles: Numero maximo de ciclos.
        height: Altura (mm).
        width: Ancho (mm).
        depth: Profundidad (mm).
    """
    __tablename__ = 'batteries'

    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id'), index=True)
    catalog = db.relationship('Catalog')

    nombre = db.Column(db.String(100), nullable=False, unique=True)
    capacity_kwh = db.Column(db.Float, nullable=False)
    power_kw = db.Column(db.Float, nullable=False)
    voltage = db.Column(db.Float, nullable=False)
    usable_kwh = db.Column(db.Float)
    dod = db.Column(db.Float)
    technology = db.Column(db.String(50))
    round_trip_efficiency = db.Column(db.Float)
    max_cycles = db.Column(db.Integer)
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)
    depth = db.Column(db.Integer)
    datasheet = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'catalog_id': self.catalog_id,
            'catalog_nombre': self.catalog.nombre if self.catalog else None,
            'nombre': self.nombre,
            'capacity_kwh': self.capacity_kwh,
            'usable_kwh': self.usable_kwh,
            'dod': self.dod,
            'power_kw': self.power_kw,
            'voltage': self.voltage,
            'technology': self.technology,
            'round_trip_efficiency': self.round_trip_efficiency,
            'max_cycles': self.max_cycles,
            'height': self.height,
            'width': self.width,
            'depth': self.depth,
            'datasheet': self.datasheet,
            **self.provenance_dict(),
        }

    def __repr__(self):
        return f'<Battery {self.nombre}>'

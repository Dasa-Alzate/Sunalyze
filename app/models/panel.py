"""Modelo de panel solar fotovoltaico."""

from app import db
from .database import BaseModel
from .provenance import ProvenanceMixin

class Panel(BaseModel, ProvenanceMixin):
    """
    Representa un panel solar con sus especificaciones tecnicas.

    Attributes:
        nombre: Nombre/modelo del panel.
        y: Eficiencia del panel (%).
        tcp: Coeficiente de temperatura de potencia (%/C).
        tcv: Coeficiente de temperatura de voltaje (%/C).
        voc: Voltaje de circuito abierto (V).
        vmp: Voltaje en el punto de maxima potencia (V).
        imp: Corriente en el punto de maxima potencia (A).
        isc: Corriente de cortocircuito (A).
        power: Potencia nominal (W).
        t_noct: Temperatura nominal de operacion de la celda (C).
        height: Altura del panel (mm).
        width: Ancho del panel (mm).
    """
    __tablename__ = 'panels'

    catalog_id = db.Column(db.Integer, db.ForeignKey('catalogs.id'), index=True)
    catalog = db.relationship('Catalog')

    nombre = db.Column(db.String(100), nullable=False, unique=True)
    voc = db.Column(db.Float, nullable=False)
    vmp = db.Column(db.Float, nullable=False)
    imp = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float)
    tcp = db.Column(db.Float)
    tcv = db.Column(db.Float)
    isc = db.Column(db.Float)
    t_noct = db.Column(db.Float)
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)
    datasheet = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'catalog_id': self.catalog_id,
            'catalog_nombre': self.catalog.nombre if self.catalog else None,
            'nombre': self.nombre,
            'y': self.y,
            'tcp': self.tcp,
            'tcv': self.tcv,
            'voc': self.voc,
            'vmp': self.vmp,
            'imp': self.imp,
            'isc': self.isc,
            'power': self.power,
            't_noct': self.t_noct,
            'height': self.height,
            'width': self.width,
            'datasheet': self.datasheet,
            **self.provenance_dict(),
        }
    
    def __repr__(self):
        return f'<Panel {self.nombre}>'
    
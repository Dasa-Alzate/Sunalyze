"""Modelo de panel solar fotovoltaico."""

from app import db
from .database import BaseModel

class Panel(BaseModel):
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
    
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    y = db.Column(db.Float, nullable=False)  # Eficiencia
    tcp = db.Column(db.Float, nullable=False)  # Coeficiente temperatura potencia
    tcv = db.Column(db.Float, nullable=False)  # Coeficiente temperatura voltaje
    voc = db.Column(db.Float, nullable=False)  # Voltaje circuito abierto
    vmp = db.Column(db.Float, nullable=False)  # Voltaje punto máxima potencia
    imp = db.Column(db.Float, nullable=False)  # Corriente punto máxima potencia
    isc = db.Column(db.Float, nullable=False)  # Corriente corto circuito
    power = db.Column(db.Float, nullable=False)  # Potencia en W
    t_noct = db.Column(db.Float, nullable=False)  # Temperatura NOCT
    height = db.Column(db.Integer, nullable=False)  # Altura en mm
    width = db.Column(db.Integer, nullable=False)  # Ancho en mm
    datasheet = db.Column(db.String(200))  # Ruta al datasheet PDF
    
    def to_dict(self):
        return {
            'id': self.id,
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
            'datasheet': self.datasheet
        }
    
    def __repr__(self):
        return f'<Panel {self.nombre}>'
    
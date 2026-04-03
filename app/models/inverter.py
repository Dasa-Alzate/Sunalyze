"""Modelo de inversor fotovoltaico."""

from app import db
from .database import BaseModel

class Inverter(BaseModel):
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
    
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    y = db.Column(db.Float, nullable=False)  # Eficiencia
    power_max = db.Column(db.Float, nullable=False)  # Potencia máxima DC
    power = db.Column(db.Float, nullable=False)  # Potencia nominal AC
    vmax = db.Column(db.Float, nullable=False)  # Voltaje máximo
    I_max_input = db.Column(db.Float, nullable=False)  # Corriente máxima entrada
    I_max_output = db.Column(db.Float, nullable=False)  # Corriente máxima salida
    datasheet = db.Column(db.String(200))  # Ruta al datasheet PDF
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'y': self.y,
            'power_max': self.power_max,
            'power': self.power,
            'vmax': self.vmax,
            'I_max_input': self.I_max_input,
            'I_max_output': self.I_max_output,
            'datasheet': self.datasheet
        }
    
    def __repr__(self):
        return f'<Inverter {self.nombre}>'
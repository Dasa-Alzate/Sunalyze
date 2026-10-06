"""Plan eléctrico de comercializadora: precios por periodo que usa el motor económico.

org_id NULL marca un plan global visible para todas las organizaciones.
"""

from app import db
from app.models.database import BaseModel, SoftDeleteMixin

PLAN_PRICE_FIELDS = (
    'precio_punta', 'precio_llano', 'precio_valle', 'precio_excedente',
    'precio_potencia_p1_dia', 'precio_potencia_p2_dia',
    'impuesto_electricidad', 'iva_pct', 'alquiler_contador_mes',
)


class ElectricityPlan(BaseModel, SoftDeleteMixin):
    __tablename__ = 'electricity_plans'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    comercializadora = db.Column(db.String(80), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    peaje = db.Column(db.String(20), nullable=False, default='2.0TD')
    precio_punta = db.Column(db.Float, nullable=False, default=0.193)
    precio_llano = db.Column(db.Float, nullable=False, default=0.135)
    precio_valle = db.Column(db.Float, nullable=False, default=0.083)
    precio_excedente = db.Column(db.Float, nullable=False, default=0.06)
    precio_potencia_p1_dia = db.Column(db.Float, nullable=False, default=0.077)
    precio_potencia_p2_dia = db.Column(db.Float, nullable=False, default=0.0077)
    impuesto_electricidad = db.Column(db.Float, nullable=False, default=0.0511)
    iva_pct = db.Column(db.Float, nullable=False, default=21.0)
    alquiler_contador_mes = db.Column(db.Float, nullable=False, default=0.81)

    @classmethod
    def visible(cls, plan_id, org_id):
        return cls.active().filter(
            cls.id == plan_id,
            db.or_(cls.org_id == org_id, cls.org_id.is_(None)),
        ).first()

    @property
    def is_global(self):
        return self.org_id is None

    def tariff(self):
        data = {field: getattr(self, field) for field in PLAN_PRICE_FIELDS}
        data['nombre'] = f'{self.comercializadora} · {self.nombre}'
        return data

    def to_dict(self):
        data = {field: getattr(self, field) for field in PLAN_PRICE_FIELDS}
        data.update({
            'id': self.id,
            'org_id': self.org_id,
            'comercializadora': self.comercializadora,
            'nombre': self.nombre,
            'peaje': self.peaje,
            'is_global': self.is_global,
        })
        return data

    def __repr__(self):
        return f'<ElectricityPlan {self.comercializadora} {self.nombre}>'

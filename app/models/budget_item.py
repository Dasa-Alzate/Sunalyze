from app.extensions import db
from .database import BaseModel

CAPITULOS = {
    1: 'Equipos',
    2: 'Instalación eléctrica',
    3: 'Estructura y montaje',
    4: 'Legalización y tramitación',
}


class BudgetItem(BaseModel):
    __tablename__ = 'budget_items'

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    capitulo = db.Column(db.Integer, nullable=False, default=1)
    descripcion = db.Column(db.String(200), nullable=False)
    unidad = db.Column(db.String(10), nullable=False, default='ud')
    cantidad = db.Column(db.Float, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False, default=0)
    orden = db.Column(db.Integer, nullable=False, default=0)

    @property
    def importe(self):
        return round((self.cantidad or 0) * (self.precio_unitario or 0), 2)

    def to_dict(self):
        return {
            'id': self.id,
            'capitulo': self.capitulo,
            'descripcion': self.descripcion,
            'unidad': self.unidad,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'importe': self.importe,
            'orden': self.orden,
        }

    def __repr__(self):
        return f'<BudgetItem p{self.project_id} c{self.capitulo} {self.descripcion[:20]}>'

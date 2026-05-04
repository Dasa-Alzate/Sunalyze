"""Workspace/tenant. Una persona o autonomo es un workspace de un solo miembro."""

from app.extensions import db
from .database import BaseModel, SoftDeleteMixin

ORG_TYPES = ('PERSONAL', 'BUSINESS')
PLANS = ('free', 'pro', 'business')


class Organization(BaseModel, SoftDeleteMixin):
    """Unico eje de propiedad de los datos.

    La diferencia entre persona/autonomo y empresa es configuracion (type +
    plan + nº de miembros), no un modelo de datos distinto.
    """
    __tablename__ = 'organizations'

    nombre = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='PERSONAL')
    plan = db.Column(db.String(20), nullable=False, default='free')
    seats = db.Column(db.Integer, nullable=False, default=1)

    memberships = db.relationship('Membership', back_populates='organization', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'type': self.type,
            'plan': self.plan,
            'seats': self.seats,
            'member_count': len(self.memberships),
        }

    def __repr__(self):
        return f'<Organization {self.nombre} ({self.type}/{self.plan})>'

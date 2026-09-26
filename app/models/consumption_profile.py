"""Perfil de consumo eléctrico: fuente original + serie canónica materializada.

Capa 1 (source): lo que el usuario entregó, intacto, por kind del CDM.
Capa 2 (fractions): 8760 fracciones horarias que suman 1 — lo único que consume
el motor. La escala (kWh anual) vive en el proyecto, no aquí. org_id NULL marca
un perfil curado global visible para todas las organizaciones.
"""

import json

from app import db
from .database import BaseModel, SoftDeleteMixin


class ConsumptionProfile(BaseModel, SoftDeleteMixin):
    __tablename__ = 'consumption_profiles'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    origin = db.Column(db.String(10), nullable=False, default='ui')
    annual_kwh_hint = db.Column(db.Float)
    cdm_version = db.Column(db.Integer, nullable=False, default=1)
    _source = db.Column('source', db.Text)
    _fractions = db.Column('fractions', db.Text)

    @property
    def source(self):
        return json.loads(self._source) if self._source else None

    @source.setter
    def source(self, value):
        self._source = json.dumps(value) if value is not None else None

    @property
    def fractions(self):
        return json.loads(self._fractions) if self._fractions else None

    @fractions.setter
    def fractions(self, value):
        self._fractions = json.dumps([round(v, 12) for v in value]) if value is not None else None

    @property
    def is_global(self):
        return self.org_id is None

    def to_dict(self, include_source=False):
        data = {
            'id': self.id,
            'name': self.name,
            'kind': self.kind,
            'origin': self.origin,
            'is_global': self.is_global,
            'annual_kwh_hint': self.annual_kwh_hint,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_source:
            data['source'] = self.source
        return data

    def __repr__(self):
        return f'<ConsumptionProfile {self.name}>'

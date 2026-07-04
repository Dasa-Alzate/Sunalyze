"""Modelo de escenario financiero por proyecto (org-scoped).

Permite varios escenarios por proyecto (p. ej. contado vs financiado). Guarda los
supuestos (`assumptions`) y el resultado cacheado (`results`) como JSON en columnas
de texto, siguiendo el patrón de `Project.resultados`. `is_default` marca el
escenario destacado del proyecto.
"""

import json

from app import db
from .database import BaseModel


class FinancialScenario(BaseModel):
    __tablename__ = 'financial_scenarios'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    _assumptions = db.Column('assumptions', db.Text)
    _results = db.Column('results', db.Text)

    @property
    def assumptions(self):
        if not self._assumptions:
            return None
        try:
            return json.loads(self._assumptions)
        except (ValueError, TypeError):
            return None

    @assumptions.setter
    def assumptions(self, value):
        self._assumptions = json.dumps(value) if value is not None else None

    @property
    def results(self):
        if not self._results:
            return None
        try:
            return json.loads(self._results)
        except (ValueError, TypeError):
            return None

    @results.setter
    def results(self, value):
        self._results = json.dumps(value) if value is not None else None

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'project_id': self.project_id,
            'name': self.name,
            'is_default': self.is_default,
            'created_by': self.created_by,
            'assumptions': self.assumptions,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<FinancialScenario {self.name} (project={self.project_id})>'

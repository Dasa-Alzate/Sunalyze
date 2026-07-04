"""Historial ligero de eventos de legalizacion de un proyecto.

Cada transicion de estado registra un evento inmutable (de->a, actor, nota,
timestamp) para auditar el avance del expediente.
"""

from app.extensions import db
from .database import BaseModel


class ProjectEvent(BaseModel):
    """Evento de transicion de estado del expediente de legalizacion."""
    __tablename__ = 'project_events'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    from_estado = db.Column(db.String(20), nullable=True)
    to_estado = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(500), nullable=True)

    actor = db.relationship('User', foreign_keys=[actor_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'actor_user_id': self.actor_user_id,
            'actor': self.actor.full_name if self.actor else None,
            'from_estado': self.from_estado,
            'to_estado': self.to_estado,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ProjectEvent p{self.project_id} {self.from_estado}->{self.to_estado}>'

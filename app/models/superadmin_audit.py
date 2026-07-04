"""Registro de auditoría de acciones del portal de superadmin.

Toda acción con efecto (aplicar migración, conceder superadmin, aprobar/lockear
equipo, tocar tickets) deja rastro: quién, desde qué IP, qué y sobre qué.
"""

from app.extensions import db
from .database import BaseModel


class SuperadminAudit(BaseModel):
    __tablename__ = 'superadmin_audit'

    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), index=True)
    actor_email = db.Column(db.String(255))
    ip = db.Column(db.String(64))
    action = db.Column(db.String(80), nullable=False, index=True)
    target = db.Column(db.String(200))
    detail = db.Column(db.Text)

    actor = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'actor_email': self.actor_email,
            'ip': self.ip,
            'action': self.action,
            'target': self.target,
            'detail': self.detail,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

"""Invitacion para incorporar a una persona a un workspace con un rol."""

import secrets
from datetime import datetime, timedelta

from app.extensions import db
from .database import BaseModel

STATUSES = ('pending', 'accepted', 'revoked')
INVITABLE_ROLES = ('admin', 'member')
DEFAULT_TTL_DAYS = 7


def _new_token():
    return secrets.token_urlsafe(32)


class Invitation(BaseModel):
    """Invitacion pendiente de aceptacion, vinculada a un email y una org."""
    __tablename__ = 'invitations'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='member')
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True, default=_new_token)
    status = db.Column(db.String(20), nullable=False, default='pending')
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    organization = db.relationship('Organization')
    invited_by = db.relationship('User', foreign_keys=[invited_by_user_id])
    accepted_user = db.relationship('User', foreign_keys=[accepted_user_id])

    @staticmethod
    def default_expiry():
        return datetime.utcnow() + timedelta(days=DEFAULT_TTL_DAYS)

    @property
    def is_expired(self):
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'invited_by_user_id': self.invited_by_user_id,
            'invited_by': self.invited_by.full_name if self.invited_by else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_user_id': self.accepted_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Invitation {self.email} -> o{self.org_id} ({self.status})>'

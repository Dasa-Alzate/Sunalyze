
import json

from app.extensions import db
from .database import BaseModel


def _link_for(entity_type, entity_id):
    if entity_type == 'project' and entity_id:
        return f'/proyectos/{entity_id}'
    if entity_type == 'membership':
        return '/equipo'
    if entity_type == 'invitation':
        return '/equipo'
    return None


class Notification(BaseModel):
    __tablename__ = 'notifications'
    __table_args__ = (
        db.Index('ix_notifications_recipient_org', 'recipient_user_id', 'org_id'),
    )

    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(80), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    entity_type = db.Column(db.String(80), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    payload = db.Column(db.Text, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True, index=True)

    @property
    def is_read(self):
        return self.read_at is not None

    def to_dict(self):
        try:
            payload = json.loads(self.payload) if self.payload else None
        except (ValueError, TypeError):
            payload = None
        return {
            'id': self.id,
            'type': self.type,
            'org_id': self.org_id,
            'actor_user_id': self.actor_user_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'payload': payload,
            'link': _link_for(self.entity_type, self.entity_id),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Notification {self.type} -> u{self.recipient_user_id} org{self.org_id}>'

"""Tickets de soporte al cliente y sus mensajes."""

from app.extensions import db
from .database import BaseModel

TICKET_STATUSES = ('open', 'pending', 'closed')
TICKET_PRIORITIES = ('low', 'normal', 'high', 'urgent')


class SupportTicket(BaseModel):
    __tablename__ = 'support_tickets'

    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open', index=True)
    priority = db.Column(db.String(20), nullable=False, default='normal')

    requester_email = db.Column(db.String(255), nullable=False)
    requester_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), index=True)

    requester = db.relationship('User')
    organization = db.relationship('Organization')
    messages = db.relationship('SupportTicketMessage', back_populates='ticket',
                               cascade='all, delete-orphan', order_by='SupportTicketMessage.created_at')

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'requester_email': self.requester_email,
            'org': self.organization.nombre if self.organization else None,
            'message_count': len(self.messages),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SupportTicketMessage(BaseModel):
    __tablename__ = 'support_ticket_messages'

    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(120), nullable=False, default='requester')
    is_staff = db.Column(db.Boolean, nullable=False, default=False)

    ticket = db.relationship('SupportTicket', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'body': self.body,
            'author': self.author,
            'is_staff': self.is_staff,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

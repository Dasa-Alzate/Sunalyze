"""Evento de auditoria append-only y org-scoped.

Fundacion general de auditoria de la app. Las filas solo se insertan, nunca se
actualizan ni se borran desde la aplicacion. `org_id` es nullable para admitir
eventos de plataforma (sin org) y permitir unificar en el futuro la bitacora de
superadmin con esta tabla.
"""

from app.extensions import db
from .database import BaseModel


class AuditEvent(BaseModel):
    """Registro inmutable de una accion sobre una entidad.

    `actor_email` se desnormaliza para que el evento sobreviva al borrado del
    usuario. `action`/`entity_type` siguen la convencion `dominio.verbo` y
    `dominio` respectivamente. `payload` guarda JSON (diff/contexto) como Text.
    """

    __tablename__ = 'audit_events'
    __table_args__ = (
        db.Index('ix_audit_events_org_created', 'org_id', 'created_at'),
    )

    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor_email = db.Column(db.String(255), nullable=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(80), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    payload = db.Column(db.Text, nullable=True)
    ip = db.Column(db.String(64), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'actor_user_id': self.actor_user_id,
            'actor_email': self.actor_email,
            'org_id': self.org_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'payload': self.payload,
            'ip': self.ip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<AuditEvent {self.action} {self.entity_type}#{self.entity_id} org{self.org_id}>'

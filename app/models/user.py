"""Usuario autenticable por correo/contraseña."""

import hashlib
import secrets

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from .database import BaseModel, SoftDeleteMixin


class User(BaseModel, SoftDeleteMixin):
    __tablename__ = 'users'

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), default='')
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    privacy_accepted_at = db.Column(db.DateTime, nullable=True)

    memberships = db.relationship('Membership', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def anonymize(self):
        """Reemplaza la PII directa por valores anonimos e irreversibles (Art. 17).

        El email pasa a un token opaco unico bajo el dominio reservado .invalid
        (RFC 2606), derivado por SHA-256 de un secreto aleatorio no almacenado, de
        modo que no es reversible y conserva la unicidad de la constraint. Invalida
        la contraseña y deja el nombre en valores neutros. Idempotente.
        """
        if self.email.endswith('@anonymized.invalid'):
            return
        digest = hashlib.sha256(f'{self.id}:{secrets.token_hex(16)}'.encode()).hexdigest()[:32]
        self.email = f'anon-{digest}@anonymized.invalid'
        self.first_name = 'Usuario'
        self.last_name = 'anonimizado'
        self.email_verified = False
        self.password_hash = generate_password_hash(secrets.token_urlsafe(32))

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def organizations(self):
        return [m.organization for m in self.memberships]

    @property
    def personal_org(self):
        for m in self.memberships:
            if m.organization and m.organization.type == 'PERSONAL':
                return m.organization
        return self.organizations[0] if self.organizations else None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email_verified': self.email_verified,
            'privacy_accepted_at': self.privacy_accepted_at.isoformat() if self.privacy_accepted_at else None,
            'organizations': [
                {**m.organization.to_dict(), 'role': m.role}
                for m in self.memberships if m.organization
            ],
        }

    def __repr__(self):
        return f'<User {self.email}>'

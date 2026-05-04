"""Usuario autenticable por correo/contraseña."""

import json

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app import mfa
from .database import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), default='')
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_superadmin = db.Column(db.Boolean, nullable=False, default=False)
    mfa_secret = db.Column(db.String(64))
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    mfa_recovery_codes = db.Column(db.Text)

    memberships = db.relationship('Membership', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def set_recovery_codes(self, codes):
        """Genera y persiste solo los hashes de una lista de códigos en claro."""
        self.mfa_recovery_codes = json.dumps([mfa.hash_recovery_code(c) for c in codes])

    def consume_recovery_code(self, code):
        """Valida y elimina un código de recuperación; True si era válido."""
        stored = json.loads(self.mfa_recovery_codes or '[]')
        for index, hashed in enumerate(stored):
            if mfa.verify_recovery_code(code, hashed):
                stored.pop(index)
                self.mfa_recovery_codes = json.dumps(stored)
                return True
        return False

    @property
    def recovery_codes_remaining(self):
        return len(json.loads(self.mfa_recovery_codes or '[]'))

    def enable_mfa(self, secret):
        """Activa MFA con el secreto confirmado y genera códigos de recuperación.

        Devuelve los códigos en claro (solo se muestran una vez)."""
        self.mfa_secret = secret
        self.mfa_enabled = True
        codes = mfa.generate_recovery_codes()
        self.set_recovery_codes(codes)
        return codes

    def verify_totp(self, code):
        return bool(self.mfa_secret) and mfa.verify_totp(self.mfa_secret, code)

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
            'is_superadmin': self.is_superadmin,
            'organizations': [
                {**m.organization.to_dict(), 'role': m.role}
                for m in self.memberships if m.organization
            ],
        }

    def __repr__(self):
        return f'<User {self.email}>'

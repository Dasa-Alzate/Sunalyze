
import json
import hashlib
import secrets
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app import mfa
from .database import BaseModel, SoftDeleteMixin

FAILED_LOGIN_THRESHOLD = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)
LOCKOUT_DURATION = timedelta(minutes=15)


class User(BaseModel, SoftDeleteMixin):
    __tablename__ = 'users'

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), default='')
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_superadmin = db.Column(db.Boolean, nullable=False, default=False)
    locale = db.Column(db.String(5), nullable=False, default='es', server_default='es')
    mfa_secret = db.Column(db.Text)
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    mfa_recovery_codes = db.Column(db.Text)
    session_gen = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    last_failed_login_at = db.Column(db.DateTime, nullable=True)
    lockout_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    privacy_accepted_at = db.Column(db.DateTime, nullable=True)

    memberships = db.relationship(
        'Membership', back_populates='user',
        cascade='all, delete-orphan', passive_deletes=True,
    )

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def revoke_sessions(self):
        self.session_gen = (self.session_gen or 0) + 1

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def set_recovery_codes(self, codes):
        self.mfa_recovery_codes = json.dumps([mfa.hash_recovery_code(c) for c in codes])

    def consume_recovery_code(self, code):
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
        self.mfa_secret = mfa.encrypt_secret(secret)
        self.mfa_enabled = True
        codes = mfa.generate_recovery_codes()
        self.set_recovery_codes(codes)
        return codes

    def verify_totp(self, code):
        secret = mfa.decrypt_secret(self.mfa_secret)
        return bool(secret) and mfa.verify_totp(secret, code)

    def is_locked_out(self, now=None):
        now = now or datetime.utcnow()
        return self.lockout_until is not None and self.lockout_until > now

    def register_failed_login(self, now=None):
        now = now or datetime.utcnow()
        if (
            self.last_failed_login_at is None
            or now - self.last_failed_login_at > LOGIN_ATTEMPT_WINDOW
        ):
            self.failed_login_count = 0
        self.failed_login_count += 1
        self.last_failed_login_at = now
        if self.failed_login_count >= FAILED_LOGIN_THRESHOLD:
            self.lockout_until = now + LOCKOUT_DURATION

    def register_successful_login(self, now=None):
        now = now or datetime.utcnow()
        self.failed_login_count = 0
        self.last_failed_login_at = None
        self.lockout_until = None
        self.last_login_at = now

    def anonymize(self):
        if self.email.endswith('@anonymized.invalid'):
            return
        digest = hashlib.sha256(f'{self.id}:{secrets.token_hex(16)}'.encode()).hexdigest()[:32]
        self.email = f'anon-{digest}@anonymized.invalid'
        self.first_name = 'Usuario'
        self.last_name = 'anonimizado'
        self.email_verified = False
        self.password_hash = generate_password_hash(secrets.token_urlsafe(32))
        self.revoke_sessions()

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
            'locale': self.locale or 'es',
            'privacy_accepted_at': self.privacy_accepted_at.isoformat() if self.privacy_accepted_at else None,
            'organizations': [
                {**m.organization.to_dict(), 'role': m.role}
                for m in self.memberships if m.organization and not m.organization.is_deleted
            ],
        }

    def __repr__(self):
        return f'<User {self.email}>'

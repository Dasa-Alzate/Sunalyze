"""Usuario autenticable por correo/contraseña."""

from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from .database import BaseModel

FAILED_LOGIN_THRESHOLD = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)
LOCKOUT_DURATION = timedelta(minutes=15)


class User(BaseModel):
    __tablename__ = 'users'

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), default='')
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    last_failed_login_at = db.Column(db.DateTime, nullable=True)
    lockout_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)

    memberships = db.relationship('Membership', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def is_locked_out(self, now=None):
        """True si la cuenta esta bloqueada por intentos fallidos."""
        now = now or datetime.utcnow()
        return self.lockout_until is not None and self.lockout_until > now

    def register_failed_login(self, now=None):
        """Suma un intento fallido (soft lockout por ventana) y bloquea al llegar al umbral.

        Si el ultimo fallo es mas antiguo que la ventana, el contador se
        reinicia antes de sumar (mitiga el lockout como vector de DoS).
        """
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
        """Resetea el estado de bloqueo y marca el ultimo acceso."""
        now = now or datetime.utcnow()
        self.failed_login_count = 0
        self.last_failed_login_at = None
        self.lockout_until = None
        self.last_login_at = now

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
            'organizations': [
                {**m.organization.to_dict(), 'role': m.role}
                for m in self.memberships if m.organization
            ],
        }

    def __repr__(self):
        return f'<User {self.email}>'

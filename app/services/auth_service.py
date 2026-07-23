
import hashlib
import logging

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.errors import Conflict, Unauthorized, NotFound, Forbidden, ValidationError
from app.db_helpers import commit_or_conflict
from app.gateways import tokens
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def register(email, password, first_name, last_name='', company=''):
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise Conflict('Ya existe una cuenta con ese correo.', code='auth.email_taken')

        user = User(email=email, first_name=first_name.strip(), last_name=last_name.strip())
        user.set_password(password)

        if company.strip():
            org = Organization(nombre=company.strip(), type='BUSINESS', plan='free', seats=5)
        else:
            org = Organization(nombre='Mi espacio', type='PERSONAL', plan='free', seats=1)

        db.session.add(user)
        db.session.add(org)
        db.session.flush()
        db.session.add(Membership(user_id=user.id, org_id=org.id, role='owner'))
        commit_or_conflict('Ya existe una cuenta con ese correo.')

        from app.services.catalog_service import CatalogService
        CatalogService.bootstrap_org(org.id)

        verify_token = tokens.issue(tokens.VERIFY_EMAIL, {'uid': user.id})
        logger.info('Usuario registrado: %s (org %s)', user.email, org.id)
        return user, verify_token

    @staticmethod
    def authenticate(email, password):
        user = User.active().filter_by(email=email.strip().lower()).first()

        if user and user.is_locked_out():
            raise Forbidden('Cuenta bloqueada temporalmente por intentos fallidos. Intenta mas tarde.', code='auth.account_locked')

        if not user or not user.check_password(password):
            if user:
                user.register_failed_login()
                db.session.commit()
            raise Unauthorized('Correo o contraseña incorrectos.', code='auth.invalid_credentials')

        user.register_successful_login()
        AuditService.record(
            'auth.login',
            actor=user,
            org_id=user.personal_org.id if user.personal_org else None,
            entity_type='user',
            entity_id=user.id,
        )
        db.session.commit()
        return user

    @staticmethod
    def find_active_by_email(email):
        return User.active().filter_by(email=email.strip().lower()).first()

    @staticmethod
    def _password_fingerprint(user):
        return hashlib.sha256((user.password_hash or '').encode('utf-8')).hexdigest()[:16]

    @staticmethod
    def request_password_reset(email):
        user = AuthService.find_active_by_email(email)
        if not user:
            return None
        return tokens.issue(
            tokens.RESET_PASSWORD,
            {'uid': user.id, 'pwd': AuthService._password_fingerprint(user)},
        )

    @staticmethod
    def reset_password(token, new_password):
        data = tokens.verify(tokens.RESET_PASSWORD, token, max_age_seconds=3600)
        user = User.active().filter_by(id=data.get('uid')).first()
        if not user:
            raise NotFound('Usuario no encontrado.', code='auth.user_not_found')
        if data.get('pwd') != AuthService._password_fingerprint(user):
            raise ValidationError('Enlace invalido o manipulado.', code='token.invalid')
        user.set_password(new_password)
        user.revoke_sessions()
        db.session.commit()
        return user

    @staticmethod
    def verify_email(token):
        data = tokens.verify(tokens.VERIFY_EMAIL, token, max_age_seconds=86400)
        user = User.active().filter_by(id=data.get('uid')).first()
        if not user:
            raise NotFound('Usuario no encontrado.', code='auth.user_not_found')
        user.email_verified = True
        db.session.commit()
        return user

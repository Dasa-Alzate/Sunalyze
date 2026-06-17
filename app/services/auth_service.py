"""Logica de dominio de autenticacion y alta de workspace.

Aisla las reglas (unicidad de correo, creacion del workspace personal,
tokens) del transporte HTTP. Devuelve modelos/tokens y lanza DomainError;
no toca request/response.
"""

import logging

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.errors import Conflict, Unauthorized, NotFound
from app.db_helpers import commit_or_conflict
from app.gateways import tokens

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def register(email, password, first_name, last_name='', company=''):
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise Conflict('Ya existe una cuenta con ese correo.')

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
        if not user or not user.check_password(password):
            raise Unauthorized('Correo o contraseña incorrectos.')
        return user

    @staticmethod
    def request_password_reset(email):
        user = User.active().filter_by(email=email.strip().lower()).first()
        if not user:
            return None
        return tokens.issue(tokens.RESET_PASSWORD, {'uid': user.id})

    @staticmethod
    def reset_password(token, new_password):
        data = tokens.verify(tokens.RESET_PASSWORD, token, max_age_seconds=3600)
        user = User.active().filter_by(id=data.get('uid')).first()
        if not user:
            raise NotFound('Usuario no encontrado.')
        user.set_password(new_password)
        db.session.commit()
        return user

    @staticmethod
    def verify_email(token):
        data = tokens.verify(tokens.VERIFY_EMAIL, token, max_age_seconds=86400)
        user = User.active().filter_by(id=data.get('uid')).first()
        if not user:
            raise NotFound('Usuario no encontrado.')
        user.email_verified = True
        db.session.commit()
        return user

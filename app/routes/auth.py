"""Endpoints de autenticacion por correo. Capa HTTP fina sobre AuthService."""

from flask import Blueprint, request, jsonify, current_app

from app.schemas.auth import RegisterSchema, LoginSchema, ForgotSchema, ResetSchema, VerifySchema, LocaleSchema
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.security import login_user, logout_user, current_user, login_required
from app.authz import current_role, current_permissions
from app.extensions import limiter, db
from app.services.flag_service import FlagService
from app.security import current_org_id
from app.i18n import resolve_locale, normalize_locale
from app.errors import ValidationError

auth_bp = Blueprint('auth', __name__)


def _session_payload(user):
    return {
        'user': user.to_dict() if user else None,
        'role': current_role() if user else None,
        'permissions': sorted(current_permissions()) if user else [],
        'flags': FlagService.resolve_all(current_org_id(), user.id) if user else {},
        'locale': resolve_locale(user),
    }


def _base_url():
    return request.host_url.rstrip('/')


def _dev_link(path):
    if not current_app.config.get('IS_PRODUCTION'):
        return f'{_base_url()}{path}'
    return None


@auth_bp.route('/api/auth/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    data = RegisterSchema(**(request.get_json(silent=True) or {}))
    user, verify_token = AuthService.register(
        data.email, data.password, data.first_name, data.last_name, data.company,
    )
    verify_path = f'/verificar?token={verify_token}'
    EmailService.send('welcome', user.email, {
        'first_name': user.first_name,
        'cta_url': f'{_base_url()}{verify_path}',
    }, locale=user.locale)
    login_user(user)
    return jsonify({**_session_payload(user), 'verify_link': _dev_link(verify_path)}), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    data = LoginSchema(**(request.get_json(silent=True) or {}))
    user = AuthService.authenticate(data.email, data.password)
    login_user(user, remember=data.remember)
    return jsonify(_session_payload(user))


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'ok': True})


@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    return jsonify(_session_payload(current_user()))


@auth_bp.route('/api/auth/me', methods=['PATCH'])
@login_required
def update_me():
    data = LocaleSchema(**(request.get_json(silent=True) or {}))
    locale = normalize_locale(data.locale)
    if not locale:
        raise ValidationError('Idioma no soportado.', code='auth.locale_unsupported')
    user = current_user()
    user.locale = locale
    db.session.commit()
    return jsonify(_session_payload(user))


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit('5 per minute')
def forgot_password():
    data = ForgotSchema(**(request.get_json(silent=True) or {}))
    token = AuthService.request_password_reset(data.email)
    dev_link = None
    if token:
        reset_path = f'/reset-password?token={token}'
        recipient = AuthService.find_active_by_email(data.email)
        EmailService.send('reset-password', data.email, {
            'reset_url': f'{_base_url()}{reset_path}',
            'expires_minutes': 60,
        }, locale=recipient.locale if recipient else None)
        dev_link = _dev_link(reset_path)
    return jsonify({'message': 'Si el correo existe, enviaremos un enlace.', 'reset_link': dev_link})


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit('10 per hour')
def reset_password():
    data = ResetSchema(**(request.get_json(silent=True) or {}))
    AuthService.reset_password(data.token, data.password)
    return jsonify({'ok': True, 'message': 'Contraseña actualizada. Ya puedes iniciar sesión.'})


@auth_bp.route('/api/auth/verify-email', methods=['POST'])
@limiter.limit('10 per hour')
def verify_email():
    data = VerifySchema(**(request.get_json(silent=True) or {}))
    user = AuthService.verify_email(data.token)
    return jsonify({'ok': True, 'user': user.to_dict()})

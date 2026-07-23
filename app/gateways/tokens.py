
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.errors import ValidationError

VERIFY_EMAIL = 'email-verify'
RESET_PASSWORD = 'password-reset'


def _serializer(salt):
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=salt)


def issue(purpose, payload):
    return _serializer(purpose).dumps(payload)


def verify(purpose, token, max_age_seconds):
    try:
        return _serializer(purpose).loads(token, max_age=max_age_seconds)
    except SignatureExpired:
        raise ValidationError('El enlace ha caducado. Solicita uno nuevo.', code='token.expired')
    except BadSignature:
        raise ValidationError('Enlace invalido o manipulado.', code='token.invalid')

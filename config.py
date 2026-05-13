import os
import logging
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_ENV = os.environ.get('FLASK_ENV', 'development').lower()
_IS_PRODUCTION = _ENV == 'production'


def _resolve_database_url():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está definida. Copia .env.example a .env y configúrala "
            "(p. ej. mysql+pymysql://usuario:password@127.0.0.1:3306/sunalyze)."
        )
    rewrites = (
        ('postgres://', 'postgresql://'),
        ('mysql://', 'mysql+pymysql://'),
    )
    for old_scheme, new_scheme in rewrites:
        if url.startswith(old_scheme):
            return new_scheme + url[len(old_scheme):]
    return url


def _resolve_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    if _IS_PRODUCTION:
        raise RuntimeError(
            "SECRET_KEY debe estar definida en producción (FLASK_ENV=production). "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    logger.warning(
        "SECRET_KEY no definida: usando una clave efímera aleatoria (las sesiones "
        "se invalidarán al reiniciar). Define SECRET_KEY en tu .env para persistirlas."
    )
    return secrets.token_hex(32)


class Config:
    SECRET_KEY = _resolve_secret_key()
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = _resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL') or None
    CACHE_DEFAULT_TIMEOUT = 300
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'
    IS_PRODUCTION = _IS_PRODUCTION

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    MFA_ENC_KEY = os.environ.get('MFA_ENC_KEY') or None

    SERVER_NAME = os.environ.get('SERVER_NAME') or None
    SUPERADMIN_SUBDOMAIN = os.environ.get('SUPERADMIN_SUBDOMAIN') or None
    SUPERADMIN_IP_ALLOWLIST = os.environ.get('SUPERADMIN_IP_ALLOWLIST', '')
    SUPERADMIN_TRUST_PROXY = os.environ.get('SUPERADMIN_TRUST_PROXY', '').lower() in ('1', 'true', 'yes')

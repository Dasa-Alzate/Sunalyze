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


def _resolve_mail_backend():
    backend = (os.environ.get('MAIL_BACKEND') or 'log').lower()
    if backend not in ('log', 'smtp'):
        raise RuntimeError(
            f"MAIL_BACKEND='{backend}' no es válido. Usa 'log' (solo registra, default) o 'smtp'."
        )
    if backend == 'smtp':
        missing = [name for name in ('MAIL_SMTP_HOST', 'MAIL_FROM') if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                'MAIL_BACKEND=smtp requiere definir: ' + ', '.join(missing) + '.'
            )
    return backend


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

    STORAGE_BACKEND = (os.environ.get('STORAGE_BACKEND') or 'local').lower()
    S3_BUCKET = os.environ.get('S3_BUCKET') or None
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL') or None
    S3_REGION = os.environ.get('S3_REGION') or None
    S3_PREFIX = os.environ.get('S3_PREFIX', 'generated')
    S3_ACCESS_KEY_ID = (
        os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('S3_ACCESS_KEY_ID') or None
    )
    S3_SECRET_ACCESS_KEY = (
        os.environ.get('AWS_SECRET_ACCESS_KEY') or os.environ.get('S3_SECRET_ACCESS_KEY') or None
    )
    S3_URL_EXPIRES = int(os.environ.get('S3_URL_EXPIRES', '3600'))

    JOB_QUEUE = (os.environ.get('JOB_QUEUE') or 'sync').lower()
    JOB_QUEUE_REDIS_URL = os.environ.get('JOB_QUEUE_REDIS_URL') or os.environ.get('REDIS_URL') or None
    JOB_QUEUE_NAME = os.environ.get('JOB_QUEUE_NAME', 'pdf')
    PDF_JOB_TIMEOUT = int(os.environ.get('PDF_JOB_TIMEOUT', '180'))
    PDF_RATELIMIT = os.environ.get('PDF_RATELIMIT', '60 per hour')

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    MFA_ENC_KEY = os.environ.get('MFA_ENC_KEY') or None

    MAIL_BACKEND = _resolve_mail_backend()
    MAIL_SMTP_HOST = os.environ.get('MAIL_SMTP_HOST') or None
    MAIL_SMTP_PORT = int(os.environ.get('MAIL_SMTP_PORT', '587'))
    MAIL_SMTP_USERNAME = os.environ.get('MAIL_SMTP_USERNAME') or None
    MAIL_SMTP_PASSWORD = os.environ.get('MAIL_SMTP_PASSWORD') or None
    MAIL_SMTP_STARTTLS = os.environ.get('MAIL_SMTP_STARTTLS', 'true').lower() in ('1', 'true', 'yes')
    MAIL_FROM = os.environ.get('MAIL_FROM') or None
    MAIL_TIMEOUT = int(os.environ.get('MAIL_TIMEOUT', '10'))

    SENTRY_DSN = os.environ.get('SENTRY_DSN') or None
    SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT') or (
        'production' if _IS_PRODUCTION else 'development'
    )
    SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.0'))

    SERVER_NAME = os.environ.get('SERVER_NAME') or None
    SUPERADMIN_SUBDOMAIN = os.environ.get('SUPERADMIN_SUBDOMAIN') or None
    SUPERADMIN_IP_ALLOWLIST = os.environ.get('SUPERADMIN_IP_ALLOWLIST', '')
    SUPERADMIN_TRUST_PROXY = os.environ.get('SUPERADMIN_TRUST_PROXY', '').lower() in ('1', 'true', 'yes')

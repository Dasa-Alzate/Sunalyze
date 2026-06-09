import os
from dotenv import load_dotenv

load_dotenv()

_ENV = os.environ.get('FLASK_ENV', 'development').lower()
_IS_PRODUCTION = _ENV == 'production'

_DEV_DB_URL = 'mysql+pymysql://root:0000@localhost/sunalyze'

_db_url = os.environ.get('DATABASE_URL')
if _db_url is None:
    if _IS_PRODUCTION:
        raise RuntimeError(
            "DATABASE_URL debe estar definida en producción (FLASK_ENV=production). "
            "Configúrala en el entorno; ver .env.example."
        )
    _db_url = _DEV_DB_URL

if _db_url.startswith('mysql://'):
    _db_url = 'mysql+pymysql://' + _db_url[len('mysql://'):]


def _resolve_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    if _IS_PRODUCTION:
        raise RuntimeError(
            "SECRET_KEY debe estar definida en producción (FLASK_ENV=production). "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return 'dev-only-insecure-key-change-in-prod'


class Config:
    SECRET_KEY = _resolve_secret_key()
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

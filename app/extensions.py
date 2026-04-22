"""Extensiones Flask como singletons, fuente unica de verdad.

Centralizarlas aqui evita los imports circulares que aparecen cuando los
modelos y la fabrica de la app comparten `db`. `app/__init__` las reexporta
para mantener compatibilidad con `from app import db`.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import MetaData

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
cache = Cache()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri='memory://', default_limits=[])

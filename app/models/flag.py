"""Feature flags: definición del flag + overrides por ámbito.

Un flag está "encendido" en un contexto si algún override lo concede, resuelto
por especificidad (user > org > global > default). El override lleva su `source`
(grant manual, experimento, dev) para poder caducar/revocar por origen; hoy el
pago no existe, pero sería una fuente más sin tocar nada.
"""

from app.extensions import db
from .database import BaseModel

SCOPES = ('global', 'org', 'user')
SOURCES = ('dev', 'grant', 'experiment')


class Flag(BaseModel):
    __tablename__ = 'flags'

    key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    titulo = db.Column(db.String(150), default='')
    descripcion = db.Column(db.String(500), default='')
    default_enabled = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default='active')

    is_visible = db.Column(db.Boolean, nullable=False, default=False)
    image_path = db.Column(db.String(255))
    thumbnail_path = db.Column(db.String(255))
    help_url = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2))

    def to_dict(self):
        return {
            'key': self.key,
            'nombre': self.nombre,
            'titulo': self.titulo or '',
            'descripcion': self.descripcion or '',
            'default_enabled': self.default_enabled,
            'status': self.status,
            'is_visible': self.is_visible,
            'image_path': self.image_path,
            'thumbnail_path': self.thumbnail_path,
            'help_url': self.help_url,
            'price': float(self.price) if self.price is not None else None,
        }

    def __repr__(self):
        return f'<Flag {self.key} default={self.default_enabled}>'


class FlagOverride(BaseModel):
    __tablename__ = 'flag_overrides'
    __table_args__ = (
        db.UniqueConstraint('flag_key', 'scope', 'scope_id', name='uq_override_flag_scope'),
    )

    flag_key = db.Column(db.String(80), db.ForeignKey('flags.key'), nullable=False, index=True)
    scope = db.Column(db.String(10), nullable=False)
    scope_id = db.Column(db.Integer, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    source = db.Column(db.String(20), nullable=False, default='grant')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'flag_key': self.flag_key,
            'scope': self.scope,
            'scope_id': self.scope_id,
            'enabled': self.enabled,
            'source': self.source,
        }

    def __repr__(self):
        return f'<FlagOverride {self.flag_key} {self.scope}:{self.scope_id}={self.enabled}>'

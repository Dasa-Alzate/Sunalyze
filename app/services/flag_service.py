"""Resolución y gestión de feature flags. Dominio sin HTTP.

Resolución por especificidad: user > org > global > default del flag.
Flag inexistente -> False (default-safe: una feature desconocida está apagada).
"""

import logging

from app.extensions import db
from app.models.flag import Flag, FlagOverride, SCOPES
from app.errors import NotFound, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_FLAGS = [
    {'key': 'geo_map', 'nombre': 'Mapa geoespacial',
     'descripcion': 'Selector de coordenadas con mapa OSM en el wizard.', 'default_enabled': True},
    {'key': 'advanced_analysis', 'nombre': 'Análisis avanzado',
     'descripcion': 'Métricas y desglose ampliado del dimensionamiento.', 'default_enabled': False},
]


class FlagService:

    @staticmethod
    def is_enabled(key, org_id=None, user_id=None):
        flag = Flag.query.filter_by(key=key, status='active').first()
        if not flag:
            return False
        overrides = {
            (o.scope, o.scope_id): o.enabled
            for o in FlagOverride.query.filter_by(flag_key=key).all()
        }
        if user_id is not None and ('user', user_id) in overrides:
            return overrides[('user', user_id)]
        if org_id is not None and ('org', org_id) in overrides:
            return overrides[('org', org_id)]
        if ('global', None) in overrides:
            return overrides[('global', None)]
        return flag.default_enabled

    @staticmethod
    def resolve_all(org_id=None, user_id=None):
        flags = Flag.query.filter_by(status='active').all()
        if not flags:
            return {}
        keys = [f.key for f in flags]
        overrides = {}
        for o in FlagOverride.query.filter(FlagOverride.flag_key.in_(keys)).all():
            overrides[(o.flag_key, o.scope, o.scope_id)] = o.enabled

        resolved = {}
        for f in flags:
            if user_id is not None and (f.key, 'user', user_id) in overrides:
                resolved[f.key] = overrides[(f.key, 'user', user_id)]
            elif org_id is not None and (f.key, 'org', org_id) in overrides:
                resolved[f.key] = overrides[(f.key, 'org', org_id)]
            elif (f.key, 'global', None) in overrides:
                resolved[f.key] = overrides[(f.key, 'global', None)]
            else:
                resolved[f.key] = f.default_enabled
        return resolved

    @staticmethod
    def list_admin():
        flags = Flag.query.order_by(Flag.key).all()
        overrides = FlagOverride.query.all()
        by_flag = {}
        for o in overrides:
            by_flag.setdefault(o.flag_key, []).append(o.to_dict())
        return [{**f.to_dict(), 'overrides': by_flag.get(f.key, [])} for f in flags]

    @staticmethod
    def upsert_flag(key, nombre, descripcion='', default_enabled=False):
        flag = Flag.query.filter_by(key=key).first()
        if flag:
            flag.nombre = nombre
            flag.descripcion = descripcion
            flag.default_enabled = default_enabled
        else:
            flag = Flag(key=key, nombre=nombre, descripcion=descripcion, default_enabled=default_enabled)
            db.session.add(flag)
        db.session.commit()
        return flag

    @staticmethod
    def set_override(key, scope, scope_id, enabled, created_by=None, source='grant'):
        if scope not in SCOPES:
            raise ValidationError(f"Ámbito inválido. Válidos: {', '.join(SCOPES)}")
        if scope == 'global':
            scope_id = None
        elif scope_id is None:
            raise ValidationError('Este ámbito requiere scope_id.')
        if not Flag.query.filter_by(key=key).first():
            raise NotFound('Flag no encontrado.')

        override = FlagOverride.query.filter_by(flag_key=key, scope=scope, scope_id=scope_id).first()
        if override:
            override.enabled = enabled
            override.source = source
        else:
            override = FlagOverride(flag_key=key, scope=scope, scope_id=scope_id,
                                    enabled=enabled, source=source, created_by=created_by)
            db.session.add(override)
        db.session.commit()
        return override

    @staticmethod
    def clear_override(key, scope, scope_id):
        if scope == 'global':
            scope_id = None
        FlagOverride.query.filter_by(flag_key=key, scope=scope, scope_id=scope_id).delete()
        db.session.commit()

    @staticmethod
    def ensure_defaults():
        created = 0
        for spec in DEFAULT_FLAGS:
            if not Flag.query.filter_by(key=spec['key']).first():
                db.session.add(Flag(**spec))
                created += 1
        db.session.commit()
        return created

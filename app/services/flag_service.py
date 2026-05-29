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
    {'key': 'geo_map', 'nombre': 'Mapa geoespacial', 'titulo': 'Mapa geoespacial',
     'descripcion': 'Selector de coordenadas con mapa OSM y geocodificación en el wizard.',
     'default_enabled': True, 'is_visible': True, 'help_url': '#', 'price': 0,
     'thumbnail_path': '/brand-logos/aiko.svg', 'image_path': '/brand-logos/aiko.svg'},
    {'key': 'advanced_analysis', 'nombre': 'Análisis avanzado', 'titulo': 'Análisis avanzado',
     'descripcion': 'Métricas y desglose ampliado del dimensionamiento, pérdidas y protecciones.',
     'default_enabled': False, 'is_visible': True, 'help_url': '#', 'price': 9.90,
     'thumbnail_path': '/brand-logos/longi.svg', 'image_path': '/brand-logos/longi.svg'},
    {'key': 'templates', 'nombre': 'Plantillas de documentos', 'titulo': 'Plantillas de documentos',
     'descripcion': 'Constructor de plantillas de documentos con variables del proyecto y biblioteca de la organización.',
     'default_enabled': False, 'is_visible': True, 'help_url': '#', 'price': 0,
     'thumbnail_path': '/brand-logos/aiko.svg', 'image_path': '/brand-logos/aiko.svg'},
    {'key': 'finance', 'nombre': 'Análisis financiero', 'titulo': 'Análisis financiero',
     'descripcion': 'Estudio económico por proyecto: payback, TIR, VAN, LCOE y CO₂ evitado, con escenarios contado vs financiado.',
     'default_enabled': False, 'is_visible': True, 'help_url': '#', 'price': 0,
     'thumbnail_path': '/brand-logos/longi.svg', 'image_path': '/brand-logos/longi.svg'},
    {'key': 'posventa', 'nombre': 'Posventa', 'titulo': 'Posventa',
     'descripcion': 'Seguimiento de instalaciones tras la entrega: estado operativo, visitas de mantenimiento, incidencias y lecturas de produccion esperado-vs-real.',
     'default_enabled': False, 'is_visible': True, 'help_url': '#', 'price': 0,
     'thumbnail_path': '/brand-logos/aiko.svg', 'image_path': '/brand-logos/aiko.svg'},
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

    _META_FIELDS = ('nombre', 'titulo', 'descripcion', 'default_enabled',
                    'is_visible', 'image_path', 'thumbnail_path', 'help_url', 'price')

    @classmethod
    def upsert_flag(cls, key, **fields):
        flag = Flag.query.filter_by(key=key).first()
        if not flag:
            flag = Flag(key=key, nombre=fields.get('nombre') or key)
            db.session.add(flag)
        for f in cls._META_FIELDS:
            if f in fields and fields[f] is not None:
                setattr(flag, f, fields[f])
        db.session.commit()
        return flag

    @staticmethod
    def marketplace(org_id=None, user_id=None):
        flags = Flag.query.filter_by(status='active', is_visible=True).order_by(Flag.titulo).all()
        return [
            {**f.to_dict(), 'enabled': FlagService.is_enabled(f.key, org_id, user_id)}
            for f in flags
        ]

    @staticmethod
    def _visible_flag(key):
        flag = Flag.query.filter_by(key=key, status='active', is_visible=True).first()
        if not flag:
            raise NotFound('Módulo no encontrado en el marketplace.')
        return flag

    @classmethod
    def enable_for_org(cls, key, org_id, created_by=None):
        cls._visible_flag(key)
        return cls.set_override(key, 'org', org_id, True, created_by=created_by, source='grant')

    @classmethod
    def disable_for_org(cls, key, org_id, created_by=None):
        cls._visible_flag(key)
        return cls.set_override(key, 'org', org_id, False, created_by=created_by, source='grant')

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

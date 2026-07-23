
import json
import logging
from importlib import import_module

from app.extensions import db
from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)

FEED_EXCLUDED_ACTIONS = ('auth.login',)

_NAME_SPECS = {
    'project': ('app.models.project', 'Project', 'cliente'),
    'catalog': ('app.models.catalog', 'Catalog', 'nombre'),
    'panel': ('app.models.panel', 'Panel', 'nombre'),
    'inverter': ('app.models.inverter', 'Inverter', 'nombre'),
    'battery': ('app.models.battery', 'Battery', 'nombre'),
    'wire': ('app.models.wire', 'Wire', 'nombre'),
    'panels': ('app.models.panel', 'Panel', 'nombre'),
    'inverters': ('app.models.inverter', 'Inverter', 'nombre'),
    'batteries': ('app.models.battery', 'Battery', 'nombre'),
    'wires': ('app.models.wire', 'Wire', 'nombre'),
    'report_template': ('app.models.report_template', 'ReportTemplate', 'name'),
    'installation': ('app.models.installation', 'Installation', None),
}

_PAYLOAD_NAME_KEYS = ('nombre', 'cliente', 'name', 'org_nombre')


def _client_ip():
    try:
        from flask import request, has_request_context
        if not has_request_context():
            return None
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.remote_addr
    except Exception:
        return None


class AuditService:

    @staticmethod
    def record(action, actor=None, org_id=None, entity_type=None,
               entity_id=None, payload=None, ip=None, actor_email=None):
        resolved_email = actor_email
        actor_user_id = None
        if actor is not None:
            actor_user_id = getattr(actor, 'id', None)
            resolved_email = resolved_email or getattr(actor, 'email', None)

        if payload is not None and not isinstance(payload, str):
            payload = json.dumps(payload, default=str, sort_keys=True)

        event = AuditEvent(
            action=action,
            actor_user_id=actor_user_id,
            actor_email=resolved_email,
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip=ip if ip is not None else _client_ip(),
        )
        db.session.add(event)
        db.session.flush()
        return event

    @staticmethod
    def list_for_org(org_id, limit=100):
        return (
            AuditEvent.query
            .filter(AuditEvent.org_id == org_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def feed_for_org(org_id, limit=50, offset=0):
        base = (
            AuditEvent.query
            .filter(AuditEvent.org_id == org_id)
            .filter(AuditEvent.action.notin_(FEED_EXCLUDED_ACTIONS))
        )
        total = base.count()
        events = (
            base
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        names = AuditService._resolve_names(events)
        items = [AuditService.to_feed_dict(e, names) for e in events]
        return {
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(events) < total,
        }

    @staticmethod
    def resolve_link(entity_type, entity_id):
        if entity_id is None or not entity_type:
            return None
        routes = {
            'project': f'/app/proyectos/{entity_id}',
            'catalog': '/app/equipos',
            'equipment': '/app/equipos',
            'panel': '/app/equipos',
            'inverter': '/app/equipos',
            'battery': '/app/equipos',
            'wire': '/app/equipos',
            'panels': '/app/equipos',
            'inverters': '/app/equipos',
            'batteries': '/app/equipos',
            'wires': '/app/equipos',
            'report_template': f'/app/plantillas/{entity_id}',
        }
        return routes.get(entity_type)

    @staticmethod
    def _resolve_names(events):
        wanted = {}
        for event in events:
            if event.entity_id is None or not event.entity_type:
                continue
            if event.entity_type in _NAME_SPECS:
                wanted.setdefault(event.entity_type, set()).add(event.entity_id)

        resolved = {}
        for entity_type, ids in wanted.items():
            module_path, class_name, attr = _NAME_SPECS[entity_type]
            try:
                model = getattr(import_module(module_path), class_name)
                base = model.with_deleted() if hasattr(model, 'with_deleted') else model.query
                for row in base.filter(model.id.in_(ids)).all():
                    resolved[(entity_type, row.id)] = AuditService._name_of(row, attr)
            except Exception:
                logger.exception('No se pudo resolver el nombre de %s', entity_type)
        return resolved

    @staticmethod
    def _name_of(row, attr):
        if attr is not None:
            return getattr(row, attr, None)
        project = getattr(row, 'project', None)
        return getattr(project, 'cliente', None) if project else None

    @staticmethod
    def _payload_name(event):
        if not event.payload:
            return None
        try:
            data = json.loads(event.payload)
        except (ValueError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        for key in _PAYLOAD_NAME_KEYS:
            value = data.get(key)
            if value:
                return value
        return None

    @staticmethod
    def _entity_label(event, names):
        name = names.get((event.entity_type, event.entity_id))
        if name:
            return name
        return AuditService._payload_name(event)

    @staticmethod
    def to_feed_dict(event, names=None):
        if names is None:
            names = AuditService._resolve_names([event])
        data = event.to_dict()
        data['link'] = AuditService.resolve_link(event.entity_type, event.entity_id)
        data['entity_label'] = AuditService._entity_label(event, names)
        return data

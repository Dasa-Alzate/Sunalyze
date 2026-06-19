"""Servicio de auditoria: escribe eventos dentro de la transaccion del cambio.

`record(...)` hace `session.add` + `flush`, pero NO `commit`. El commit lo
ejecuta el llamador junto con su propia mutacion, de modo que el evento de
auditoria y el cambio que describe son atomicos: si el cambio hace rollback, el
evento tambien desaparece.

La IP y el correo del actor se resuelven de forma defensiva: el servicio
funciona aunque se invoque fuera de un contexto de request (p. ej. en tests o
tareas), en cuyo caso esos campos quedan a None salvo que se pasen explicitos.
"""

import json
import logging

from app.extensions import db
from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


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
        """Inserta un AuditEvent en la sesion actual y hace flush (sin commit).

        Devuelve el evento creado. Acepta `actor` (modelo User) del que extrae
        id/email, o `actor_email` explicito para actores ajenos a la tabla
        `users`. `payload` puede ser dict/lista (se serializa a JSON) o str.
        """
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
        """Lee la bitacora de una org, mas reciente primero."""
        return (
            AuditEvent.query
            .filter(AuditEvent.org_id == org_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .all()
        )

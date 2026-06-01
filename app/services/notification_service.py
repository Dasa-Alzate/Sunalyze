"""Servicio de notificaciones: fan-out on write y lectura por-usuario.

`notify(...)` hace `add`+`flush` (sin commit), igual que AuditService: el commit
lo ejecuta el service de dominio junto a su mutacion, de modo que la
notificacion y el cambio que la origina son atomicos. Crea una fila por
destinatario (fan-out) y nunca notifica al propio actor.

La lectura esta scoped al usuario y al workspace activos; un usuario solo ve y
marca sus propias notificaciones (IDOR -> NotFound -> 404).
"""

import json
import logging
from datetime import datetime

from app.extensions import db
from app.models.notification import Notification
from app.errors import NotFound

logger = logging.getLogger(__name__)

_DEFAULT_PER_PAGE = 20
_MAX_PER_PAGE = 100


def _user_id(value):
    if value is None:
        return None
    return getattr(value, 'id', value)


class NotificationService:

    @staticmethod
    def notify(recipients, type, actor=None, org_id=None,
               entity_type=None, entity_id=None, payload=None):
        """Crea una notificacion por destinatario (fan-out) y hace flush.

        `recipients` admite ids o modelos User. Se deduplican los ids y se
        excluye al actor. Devuelve las notificaciones creadas (sin commit).
        """
        actor_id = _user_id(actor)

        unique = []
        seen = set()
        for r in recipients or []:
            rid = _user_id(r)
            if rid is None or rid == actor_id or rid in seen:
                continue
            seen.add(rid)
            unique.append(rid)

        if payload is not None and not isinstance(payload, str):
            payload = json.dumps(payload, default=str, sort_keys=True)

        created = []
        for rid in unique:
            notification = Notification(
                recipient_user_id=rid,
                org_id=org_id,
                type=type,
                actor_user_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
            db.session.add(notification)
            created.append(notification)

        if created:
            db.session.flush()
        return created

    @staticmethod
    def _scoped(user_id, org_id):
        return Notification.query.filter(
            Notification.recipient_user_id == user_id,
            Notification.org_id == org_id,
        )

    @staticmethod
    def list_for(user_id, org_id, page=1, per_page=_DEFAULT_PER_PAGE):
        page = max(1, int(page or 1))
        per_page = max(1, min(int(per_page or _DEFAULT_PER_PAGE), _MAX_PER_PAGE))
        query = (
            NotificationService._scoped(user_id, org_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return {
            'items': [n.to_dict() for n in items],
            'page': page,
            'per_page': per_page,
            'total': total,
            'unread_count': NotificationService.unread_count(user_id, org_id),
        }

    @staticmethod
    def unread_count(user_id, org_id):
        return (
            NotificationService._scoped(user_id, org_id)
            .filter(Notification.read_at.is_(None))
            .count()
        )

    @staticmethod
    def mark_read(user_id, org_id, notification_id):
        notification = (
            NotificationService._scoped(user_id, org_id)
            .filter(Notification.id == notification_id)
            .first()
        )
        if not notification:
            raise NotFound('Notificacion no encontrada.')
        if notification.read_at is None:
            notification.read_at = datetime.utcnow()
            db.session.commit()
        return notification

    @staticmethod
    def mark_all_read(user_id, org_id):
        updated = (
            NotificationService._scoped(user_id, org_id)
            .filter(Notification.read_at.is_(None))
            .update({'read_at': datetime.utcnow()}, synchronize_session=False)
        )
        db.session.commit()
        return updated

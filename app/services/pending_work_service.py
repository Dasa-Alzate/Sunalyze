"""Trabajo pendiente DERIVADO del estado actual: nunca se persiste.

Regla de oro: el pendiente no se almacena como filas; se calcula al vuelo
consultando el estado vigente (proyectos, invitaciones, cuenta). Cada check es
una funcion `(user, org_id) -> {type,label,count,link}`; el endpoint ejecuta el
registro y devuelve los items con `count > 0`. Cambiar el estado (p. ej. sacar
un proyecto de borrador) hace que el item desaparezca sin tocar ninguna tabla.

El badge de "trabajo pendiente" usa esta misma fuente (suma de counts), no un
contador separado.
"""

from datetime import datetime

from app.models.project import Project
from app.models.invitation import Invitation
from app.models.memoria_signature import MemoriaSignature


def _draft_projects(user, org_id):
    count = Project.query.filter(
        Project.org_id == org_id,
        Project.estado == 'borrador',
    ).count()
    return {
        'type': 'projects.draft',
        'label': 'Proyectos en borrador',
        'count': count,
        'link': '/proyectos?estado=borrador',
    }


def _stale_analysis(user, org_id):
    count = Project.query.filter(
        Project.org_id == org_id,
        Project.estado.in_(('borrador', 'en_revision')),
        Project._resultados.is_(None),
    ).count()
    return {
        'type': 'analysis.stale',
        'label': 'Proyectos sin analisis actualizado',
        'count': count,
        'link': '/proyectos',
    }


def _pending_invitations(user, org_id):
    count = Invitation.query.filter(
        Invitation.org_id == org_id,
        Invitation.status == 'pending',
        Invitation.expires_at > datetime.utcnow(),
    ).count()
    return {
        'type': 'invitations.pending',
        'label': 'Invitaciones pendientes',
        'count': count,
        'link': '/equipo',
    }


def _email_unverified(user, org_id):
    count = 0 if (user and user.email_verified) else 1
    return {
        'type': 'account.email_unverified',
        'label': 'Correo sin verificar',
        'count': count,
        'link': '/cuenta',
    }


def _missing_memoria(user, org_id):
    signed_project_ids = (
        MemoriaSignature.query
        .filter(MemoriaSignature.org_id == org_id, MemoriaSignature.is_current.is_(True))
        .with_entities(MemoriaSignature.project_id)
    )
    count = Project.query.filter(
        Project.org_id == org_id,
        Project.estado.in_(('borrador', 'en_revision')),
        Project.id.notin_(signed_project_ids),
    ).count()
    return {
        'type': 'memoria.missing',
        'label': 'Memorias tecnicas sin firmar',
        'count': count,
        'link': '/proyectos',
    }


class PendingWorkService:

    CHECKS = (
        _draft_projects,
        _stale_analysis,
        _pending_invitations,
        _email_unverified,
        _missing_memoria,
    )

    @staticmethod
    def derive(user, org_id):
        """Ejecuta los checks y devuelve los items con trabajo pendiente.

        No persiste nada: cada llamada refleja el estado actual.
        """
        items = []
        for check in PendingWorkService.CHECKS:
            item = check(user, org_id)
            if item and item.get('count', 0) > 0:
                items.append(item)
        return {
            'items': items,
            'total': sum(i['count'] for i in items),
        }

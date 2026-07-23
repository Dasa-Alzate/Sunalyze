
import hashlib
import logging

from app.extensions import db
from app.models.project import Project, ESTADOS
from app.models.memoria_signature import MemoriaSignature
from app.models.project_event import ProjectEvent
from app.models.membership import Membership
from app.errors import NotFound, ValidationError, Conflict
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

INITIAL_ESTADO = 'borrador'

TRANSITIONS = {
    'borrador': {'en_revision'},
    'en_revision': {'borrador', 'presentado', 'rechazado'},
    'presentado': {'aprobado', 'rechazado', 'en_revision'},
    'aprobado': set(),
    'rechazado': {'borrador'},
}

_REQUIRES_SIGNED_MEMORIA = {'en_revision', 'presentado'}


class LegalizationService:

    @staticmethod
    def allowed_transitions(estado):
        return TRANSITIONS.get(estado, set())

    @staticmethod
    def can_transition(from_estado, to_estado):
        return to_estado in LegalizationService.allowed_transitions(from_estado)

    @staticmethod
    def hash_pdf(pdf_bytes):
        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def history(project):
        return [event.to_dict() for event in project.events]

    @staticmethod
    def state_summary(project):
        return {
            'estado': project.estado,
            'memoria_firmada': project.current_signature is not None,
            'firma': project.current_signature.to_dict() if project.current_signature else None,
            'transiciones_posibles': sorted(
                LegalizationService.allowed_transitions(project.estado)
            ),
        }

    @staticmethod
    def sign_memoria(project, user, pdf_sha256, pdf_size_bytes, note=None):
        if not pdf_sha256:
            raise ValidationError('Hash del PDF requerido para firmar la memoria.', code='memoria.hash_required')

        for previous in project.signatures:
            previous.is_current = False

        signature = MemoriaSignature(
            org_id=project.org_id,
            project_id=project.id,
            signed_by_user_id=user.id if user else None,
            pdf_sha256=pdf_sha256.lower(),
            pdf_size_bytes=pdf_size_bytes or 0,
            is_current=True,
        )
        db.session.add(signature)
        db.session.add(LegalizationService._event(
            project, user, project.estado, project.estado,
            note or 'Memoria tecnica firmada.',
        ))
        recipients = [
            m.user_id for m in
            Membership.query.filter(Membership.org_id == project.org_id).all()
        ]
        NotificationService.notify(
            recipients, 'memoria.signed', actor=user, org_id=project.org_id,
            entity_type='project', entity_id=project.id,
            payload={'cliente': project.cliente, 'pdf_sha256': signature.pdf_sha256},
        )
        db.session.commit()
        logger.info('Memoria firmada p%s por u%s', project.id,
                    user.id if user else None)
        return signature

    @staticmethod
    def transition(project, user, to_estado, note=None):
        if to_estado not in ESTADOS:
            raise ValidationError(
                f"Estado invalido. Validos: {', '.join(ESTADOS)}"
            )

        from_estado = project.estado

        if to_estado == from_estado:
            raise Conflict(f"El proyecto ya esta en estado '{to_estado}'.", code='legalization.same_estado')

        if not LegalizationService.can_transition(from_estado, to_estado):
            allowed = sorted(LegalizationService.allowed_transitions(from_estado))
            raise Conflict(
                f"Transicion no permitida de '{from_estado}' a '{to_estado}'. "
                f"Permitidas: {', '.join(allowed) or 'ninguna'}."
            )

        if to_estado in _REQUIRES_SIGNED_MEMORIA and project.current_signature is None:
            raise Conflict(
                'No se puede avanzar el expediente sin la memoria tecnica firmada.'
            )

        project.estado = to_estado

        if to_estado == 'borrador':
            for signature in project.signatures:
                signature.is_current = False

        db.session.add(LegalizationService._event(
            project, user, from_estado, to_estado, note,
        ))
        db.session.commit()
        logger.info('Transicion p%s %s -> %s por u%s', project.id, from_estado,
                    to_estado, user.id if user else None)
        return project

    @staticmethod
    def _event(project, user, from_estado, to_estado, note):
        return ProjectEvent(
            org_id=project.org_id,
            project_id=project.id,
            actor_user_id=user.id if user else None,
            from_estado=from_estado,
            to_estado=to_estado,
            note=note,
        )

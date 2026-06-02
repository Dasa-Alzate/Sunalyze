"""Maquina de estados de legalizacion del expediente fotovoltaico (sin Flask).

Modela el ciclo administrativo del proyecto en Espana (RD 244/2019, REBT):

    borrador -> en_revision -> presentado -> aprobado
                                          -> rechazado

Concentra las transiciones permitidas y sus guardas (p. ej. no avanzar sin la
memoria tecnica firmada) lejos del transporte HTTP. Devuelve modelos y lanza
DomainError. La firma de memoria registra firmante, timestamp y un hash SHA-256
del PDF generado como prueba de integridad.
"""

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
        """Estados destino validos desde `estado` (vacio si terminal/desconocido)."""
        return TRANSITIONS.get(estado, set())

    @staticmethod
    def can_transition(from_estado, to_estado):
        return to_estado in LegalizationService.allowed_transitions(from_estado)

    @staticmethod
    def hash_pdf(pdf_bytes):
        """SHA-256 hex de los bytes del PDF de la memoria."""
        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def history(project):
        """Eventos de transicion del proyecto, mas recientes primero."""
        return [event.to_dict() for event in project.events]

    @staticmethod
    def state_summary(project):
        """Estado actual, transiciones posibles y si la memoria esta firmada."""
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
        """Registra la firma vigente de la memoria del proyecto.

        Marca cualquier firma previa como no vigente (historico) y crea la nueva
        como `is_current`. Deja constancia en el historial de eventos.
        """
        if not pdf_sha256:
            raise ValidationError('Hash del PDF requerido para firmar la memoria.')

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
        """Aplica una transicion de estado validando reglas y guardas.

        Lanza ValidationError si el destino no es un estado conocido, Conflict si
        la transicion no esta permitida desde el estado actual, y Conflict si la
        guarda de memoria firmada no se cumple.
        """
        if to_estado not in ESTADOS:
            raise ValidationError(
                f"Estado invalido. Validos: {', '.join(ESTADOS)}"
            )

        from_estado = project.estado

        if to_estado == from_estado:
            raise Conflict(f"El proyecto ya esta en estado '{to_estado}'.")

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

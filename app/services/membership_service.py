"""Logica de dominio de equipo: invitaciones, roles y miembros.

Concentra todas las invariantes (siempre >=1 owner, nadie concede un rol
superior al suyo, un admin no toca a un owner, la org PERSONAL es de un solo
asiento) lejos del transporte HTTP. Devuelve modelos y lanza DomainError.
"""

import logging
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.invitation import Invitation, INVITABLE_ROLES
from app.errors import ValidationError, NotFound, Forbidden, Conflict
from app.db_helpers import commit_or_conflict
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

_RANK = {'member': 1, 'admin': 2, 'owner': 3}


class MembershipService:

    @staticmethod
    def _org(org_id):
        org = Organization.query.get(org_id)
        if not org:
            raise NotFound('Workspace no encontrado.')
        return org

    @staticmethod
    def _membership(org_id, user_id):
        return Membership.query.filter_by(org_id=org_id, user_id=user_id).first()

    @staticmethod
    def _owner_count(org_id):
        return Membership.query.filter_by(org_id=org_id, role='owner').count()

    @staticmethod
    def team(org_id):
        org = MembershipService._org(org_id)
        memberships = Membership.query.filter_by(org_id=org_id).all()
        members = []
        for m in memberships:
            user = m.user
            members.append({
                'membership_id': m.id,
                'user_id': m.user_id,
                'role': m.role,
                'email': user.email if user else None,
                'full_name': user.full_name if user else None,
            })
        members.sort(key=lambda x: (-_RANK.get(x['role'], 0), x['full_name'] or ''))
        invitations = (
            Invitation.query
            .filter_by(org_id=org_id, status='pending')
            .order_by(Invitation.created_at.desc())
            .all()
        )
        return {
            'org': org.to_dict(),
            'members': members,
            'invitations': [i.to_dict() for i in invitations if not i.is_expired],
        }

    @staticmethod
    def invite(org_id, inviter, email, role):
        if role not in INVITABLE_ROLES:
            raise ValidationError('Rol de invitación no válido.')
        org = MembershipService._org(org_id)
        if org.type == 'PERSONAL':
            raise ValidationError('Un espacio personal no admite invitaciones.')

        inviter_membership = MembershipService._membership(org_id, inviter.id)
        if not inviter_membership:
            raise Forbidden('No perteneces a este workspace.')
        if _RANK[role] > _RANK[inviter_membership.role]:
            raise Forbidden('No puedes invitar con un rol superior al tuyo.')

        email = email.strip().lower()

        existing_user = User.query.filter_by(email=email).first()
        if existing_user and MembershipService._membership(org_id, existing_user.id):
            raise Conflict('Esa persona ya es miembro del workspace.')

        pending = Invitation.query.filter_by(
            org_id=org_id, email=email, status='pending',
        ).first()
        if pending and not pending.is_expired:
            raise Conflict('Ya existe una invitación pendiente para ese correo.')

        member_count = Membership.query.filter_by(org_id=org_id).count()
        pending_count = (
            Invitation.query
            .filter(
                Invitation.org_id == org_id,
                Invitation.status == 'pending',
                Invitation.expires_at > datetime.utcnow(),
            )
            .count()
        )
        if member_count + pending_count >= org.seats:
            raise Conflict('No quedan asientos disponibles en el plan.')

        invitation = Invitation(
            org_id=org_id,
            email=email,
            role=role,
            invited_by_user_id=inviter.id,
            expires_at=Invitation.default_expiry(),
        )
        db.session.add(invitation)
        db.session.commit()
        logger.info('Invitación creada %s -> org %s (%s)', email, org_id, role)
        return invitation

    @staticmethod
    def revoke(org_id, invitation_id):
        invitation = Invitation.query.filter_by(id=invitation_id, org_id=org_id).first()
        if not invitation:
            raise NotFound('Invitación no encontrada.')
        if invitation.status != 'pending':
            raise Conflict('La invitación ya no está pendiente.')
        invitation.status = 'revoked'
        db.session.commit()
        return invitation

    @staticmethod
    def get_by_token(token):
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            raise NotFound('Invitación no encontrada.')
        return invitation

    @staticmethod
    def accept(token, user):
        invitation = MembershipService.get_by_token(token)
        if invitation.status == 'accepted':
            raise Conflict('Esta invitación ya fue aceptada.')
        if invitation.status == 'revoked':
            raise Conflict('Esta invitación fue revocada.')
        if invitation.is_expired:
            raise ValidationError('La invitación ha caducado.')
        if MembershipService._membership(invitation.org_id, user.id):
            raise Conflict('Ya eres miembro de este workspace.')

        claimed = (
            Invitation.query
            .filter_by(id=invitation.id, status='pending')
            .update({'status': 'accepted', 'accepted_user_id': user.id}, synchronize_session=False)
        )
        if not claimed:
            raise Conflict('Esta invitación ya fue procesada.')

        db.session.add(Membership(
            user_id=user.id,
            org_id=invitation.org_id,
            role=invitation.role,
        ))
        commit_or_conflict('Ya eres miembro de este workspace.')
        logger.info('Invitación aceptada %s -> org %s', user.email, invitation.org_id)
        return MembershipService._membership(invitation.org_id, user.id)

    @staticmethod
    def change_role(org_id, actor, target_user_id, new_role):
        if new_role not in _RANK:
            raise ValidationError('Rol no válido.')
        actor_membership = MembershipService._membership(org_id, actor.id)
        if not actor_membership:
            raise Forbidden('No perteneces a este workspace.')
        target = MembershipService._membership(org_id, target_user_id)
        if not target:
            raise NotFound('Miembro no encontrado.')

        if _RANK[target.role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes gestionar a alguien con un rol superior al tuyo.')
        if _RANK[new_role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes conceder un rol superior al tuyo.')
        if new_role == 'owner' and actor_membership.role != 'owner':
            raise Forbidden('Solo un propietario puede transferir la propiedad.')

        if target.role == new_role:
            return target

        if target.role == 'owner' and new_role != 'owner' and MembershipService._owner_count(org_id) <= 1:
            raise Conflict('El workspace debe tener al menos un propietario.')

        previous_role = target.role
        target.role = new_role
        AuditService.record(
            'membership.change_role', actor=actor, org_id=org_id,
            entity_type='membership', entity_id=target.id,
            payload={'target_user_id': target_user_id, 'from': previous_role, 'to': new_role},
        )
        db.session.commit()
        logger.info('Rol cambiado u%s -> %s en org %s', target_user_id, new_role, org_id)
        return target

    @staticmethod
    def remove(org_id, actor, target_user_id):
        actor_membership = MembershipService._membership(org_id, actor.id)
        if not actor_membership:
            raise Forbidden('No perteneces a este workspace.')
        target = MembershipService._membership(org_id, target_user_id)
        if not target:
            raise NotFound('Miembro no encontrado.')

        if _RANK[target.role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes expulsar a alguien con un rol superior al tuyo.')
        if target.role == 'owner' and MembershipService._owner_count(org_id) <= 1:
            raise Conflict('No puedes expulsar al último propietario del workspace.')

        AuditService.record(
            'membership.remove', actor=actor, org_id=org_id,
            entity_type='membership', entity_id=target.id,
            payload={'target_user_id': target_user_id, 'role': target.role},
        )
        db.session.delete(target)
        db.session.commit()
        logger.info('Miembro expulsado u%s de org %s', target_user_id, org_id)
        return True

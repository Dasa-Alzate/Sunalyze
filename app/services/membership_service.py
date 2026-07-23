
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
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

_RANK = {'member': 1, 'admin': 2, 'owner': 3}


class MembershipService:

    @staticmethod
    def _org(org_id):
        org = Organization.query.get(org_id)
        if not org:
            raise NotFound('Workspace no encontrado.', code='workspace.not_found')
        return org

    @staticmethod
    def _membership(org_id, user_id):
        return Membership.query.filter_by(org_id=org_id, user_id=user_id).first()

    @staticmethod
    def _owner_count(org_id):
        return Membership.query.filter_by(org_id=org_id, role='owner').count()

    @staticmethod
    def workspaces(user, active_org_id=None):
        items = []
        for m in user.memberships:
            org = m.organization
            if not org or org.is_deleted:
                continue
            items.append({
                'org_id': org.id,
                'nombre': org.nombre,
                'type': org.type,
                'role': m.role,
                'active': org.id == active_org_id,
            })
        items.sort(key=lambda x: (not x['active'], x['nombre'] or ''))
        return items

    @staticmethod
    def switch_workspace(user, org_id):
        membership = MembershipService._membership(org_id, user.id)
        org = membership.organization if membership else None
        if not membership or not org or org.is_deleted:
            raise NotFound('Workspace no encontrado.', code='workspace.not_found')
        AuditService.record(
            'workspace.switch', actor=user, org_id=org_id,
            entity_type='organization', entity_id=org_id,
            payload={'org_nombre': org.nombre, 'role': membership.role},
        )
        db.session.commit()
        logger.info('Workspace cambiado u%s -> org %s', user.id, org_id)
        return membership

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
            raise ValidationError('Rol de invitación no válido.', code='invitation.invalid_role')
        org = MembershipService._org(org_id)
        if org.type == 'PERSONAL':
            raise ValidationError('Un espacio personal no admite invitaciones.', code='invitation.personal_space')

        inviter_membership = MembershipService._membership(org_id, inviter.id)
        if not inviter_membership:
            raise Forbidden('No perteneces a este workspace.', code='workspace.not_member')
        if _RANK[role] > _RANK[inviter_membership.role]:
            raise Forbidden('No puedes invitar con un rol superior al tuyo.', code='invitation.role_too_high')

        email = email.strip().lower()

        existing_user = User.query.filter_by(email=email).first()
        if existing_user and MembershipService._membership(org_id, existing_user.id):
            raise Conflict('Esa persona ya es miembro del workspace.', code='invitation.already_member')

        pending = Invitation.query.filter_by(
            org_id=org_id, email=email, status='pending',
        ).first()
        if pending and not pending.is_expired:
            raise Conflict('Ya existe una invitación pendiente para ese correo.', code='invitation.already_pending')

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
            raise Conflict('No quedan asientos disponibles en el plan.', code='workspace.no_seats')

        invitation = Invitation(
            org_id=org_id,
            email=email,
            role=role,
            invited_by_user_id=inviter.id,
            expires_at=Invitation.default_expiry(),
        )
        db.session.add(invitation)
        db.session.flush()
        if existing_user:
            NotificationService.notify(
                [existing_user.id], 'invitation.received', actor=inviter,
                org_id=org_id, entity_type='invitation', entity_id=invitation.id,
                payload={'org_nombre': org.nombre, 'role': role,
                         'inviter': inviter.full_name},
            )
        db.session.commit()
        logger.info('Invitación creada %s -> org %s (%s)', email, org_id, role)
        return invitation

    @staticmethod
    def revoke(org_id, invitation_id):
        invitation = Invitation.query.filter_by(id=invitation_id, org_id=org_id).first()
        if not invitation:
            raise NotFound('Invitación no encontrada.', code='invitation.not_found')
        if invitation.status != 'pending':
            raise Conflict('La invitación ya no está pendiente.', code='invitation.not_pending')
        invitation.status = 'revoked'
        db.session.commit()
        return invitation

    @staticmethod
    def get_by_token(token):
        invitation = Invitation.query.filter_by(token=token).first()
        if not invitation:
            raise NotFound('Invitación no encontrada.', code='invitation.not_found')
        return invitation

    @staticmethod
    def accept(token, user):
        invitation = MembershipService.get_by_token(token)
        if invitation.status == 'accepted':
            raise Conflict('Esta invitación ya fue aceptada.', code='invitation.already_accepted')
        if invitation.status == 'revoked':
            raise Conflict('Esta invitación fue revocada.', code='invitation.revoked')
        if invitation.is_expired:
            raise ValidationError('La invitación ha caducado.', code='invitation.expired')
        if MembershipService._membership(invitation.org_id, user.id):
            raise Conflict('Ya eres miembro de este workspace.', code='invitation.already_member')

        claimed = (
            Invitation.query
            .filter_by(id=invitation.id, status='pending')
            .update({'status': 'accepted', 'accepted_user_id': user.id}, synchronize_session=False)
        )
        if not claimed:
            raise Conflict('Esta invitación ya fue procesada.', code='invitation.already_processed')

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
            raise ValidationError('Rol no válido.', code='membership.invalid_role')
        actor_membership = MembershipService._membership(org_id, actor.id)
        if not actor_membership:
            raise Forbidden('No perteneces a este workspace.', code='workspace.not_member')
        target = MembershipService._membership(org_id, target_user_id)
        if not target:
            raise NotFound('Miembro no encontrado.', code='membership.not_found')

        if _RANK[target.role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes gestionar a alguien con un rol superior al tuyo.', code='membership.target_role_too_high')
        if _RANK[new_role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes conceder un rol superior al tuyo.', code='membership.grant_role_too_high')
        if new_role == 'owner' and actor_membership.role != 'owner':
            raise Forbidden('Solo un propietario puede transferir la propiedad.', code='membership.owner_only_transfer')

        if target.role == new_role:
            return target

        if target.role == 'owner' and new_role != 'owner' and MembershipService._owner_count(org_id) <= 1:
            raise Conflict('El workspace debe tener al menos un propietario.', code='membership.last_owner')

        previous_role = target.role
        target.role = new_role
        AuditService.record(
            'membership.change_role', actor=actor, org_id=org_id,
            entity_type='membership', entity_id=target.id,
            payload={'target_user_id': target_user_id, 'from': previous_role, 'to': new_role},
        )
        NotificationService.notify(
            [target_user_id], 'membership.role_changed', actor=actor,
            org_id=org_id, entity_type='membership', entity_id=target.id,
            payload={'from': previous_role, 'to': new_role},
        )
        db.session.commit()
        logger.info('Rol cambiado u%s -> %s en org %s', target_user_id, new_role, org_id)
        return target

    @staticmethod
    def remove(org_id, actor, target_user_id):
        actor_membership = MembershipService._membership(org_id, actor.id)
        if not actor_membership:
            raise Forbidden('No perteneces a este workspace.', code='workspace.not_member')
        target = MembershipService._membership(org_id, target_user_id)
        if not target:
            raise NotFound('Miembro no encontrado.', code='membership.not_found')

        if _RANK[target.role] > _RANK[actor_membership.role]:
            raise Forbidden('No puedes expulsar a alguien con un rol superior al tuyo.', code='membership.target_role_too_high')
        if target.role == 'owner' and MembershipService._owner_count(org_id) <= 1:
            raise Conflict('No puedes expulsar al último propietario del workspace.', code='membership.last_owner')

        AuditService.record(
            'membership.remove', actor=actor, org_id=org_id,
            entity_type='membership', entity_id=target.id,
            payload={'target_user_id': target_user_id, 'role': target.role},
        )
        NotificationService.notify(
            [target_user_id], 'membership.removed', actor=actor,
            org_id=org_id, entity_type='membership', entity_id=None,
            payload={'role': target.role, 'org_id': org_id},
        )
        db.session.delete(target)
        db.session.commit()
        logger.info('Miembro expulsado u%s de org %s', target_user_id, org_id)
        return True

"""Endpoints de equipo: miembros e invitaciones. Capa HTTP fina."""

from flask import Blueprint, request, jsonify, current_app

from app.schemas.members import InviteSchema, ChangeRoleSchema
from app.services.membership_service import MembershipService
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from app.security import current_user, current_org_id, set_current_org, login_required
from app.authz import require_permission, Permission

members_bp = Blueprint('members', __name__)


def _base_url():
    return request.host_url.rstrip('/')


def _dev_link(path):
    if not current_app.config.get('IS_PRODUCTION'):
        return f'{_base_url()}{path}'
    return None


@members_bp.route('/api/members', methods=['GET'])
@login_required
def list_team():
    return jsonify(MembershipService.team(current_org_id()))


@members_bp.route('/api/invitations', methods=['POST'])
@require_permission(Permission.MEMBER_INVITE)
def create_invitation():
    data = InviteSchema(**(request.get_json(silent=True) or {}))
    invitation = MembershipService.invite(current_org_id(), current_user(), data.email, data.role)
    accept_path = f'/invitacion?token={invitation.token}'
    invitee = AuthService.find_active_by_email(invitation.email)
    recipient_locale = invitee.locale if invitee else current_user().locale
    EmailService.send('invitation', invitation.email, {
        'org_nombre': invitation.organization.nombre if invitation.organization else 'Sunalyze',
        'inviter': current_user().full_name,
        'role': invitation.role,
        'accept_url': f'{_base_url()}{accept_path}',
    }, locale=recipient_locale)
    return jsonify({**invitation.to_dict(), 'accept_link': _dev_link(accept_path)}), 201


@members_bp.route('/api/invitations/<int:invitation_id>', methods=['DELETE'])
@require_permission(Permission.MEMBER_INVITE)
def revoke_invitation(invitation_id):
    MembershipService.revoke(current_org_id(), invitation_id)
    return jsonify({'ok': True, 'message': 'Invitación revocada.'})


@members_bp.route('/api/invitations/<token>', methods=['GET'])
@login_required
def get_invitation(token):
    invitation = MembershipService.get_by_token(token)
    return jsonify({
        'email': invitation.email,
        'role': invitation.role,
        'status': invitation.status,
        'expired': invitation.is_expired,
        'org_nombre': invitation.organization.nombre if invitation.organization else None,
        'inviter': invitation.invited_by.full_name if invitation.invited_by else None,
    })


@members_bp.route('/api/invitations/<token>/accept', methods=['POST'])
@login_required
def accept_invitation(token):
    membership = MembershipService.accept(token, current_user())
    set_current_org(membership.org_id)
    return jsonify({'ok': True, 'org_id': membership.org_id, 'role': membership.role}), 201


@members_bp.route('/api/members/<int:user_id>', methods=['PATCH'])
@require_permission(Permission.MEMBER_MANAGE)
def change_member_role(user_id):
    data = ChangeRoleSchema(**(request.get_json(silent=True) or {}))
    membership = MembershipService.change_role(current_org_id(), current_user(), user_id, data.role)
    return jsonify({'ok': True, 'user_id': membership.user_id, 'role': membership.role})


@members_bp.route('/api/members/<int:user_id>', methods=['DELETE'])
@require_permission(Permission.MEMBER_MANAGE)
def remove_member(user_id):
    MembershipService.remove(current_org_id(), current_user(), user_id)
    return jsonify({'ok': True, 'message': 'Miembro expulsado.'})

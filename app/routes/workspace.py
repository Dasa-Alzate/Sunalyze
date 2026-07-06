"""Endpoints de workspace: listado y cambio del workspace activo.

El workspace activo vive en la sesion (`session['org_id']`, la fuente que
resuelve `current_org_id()`); cambiarlo re-escopa todas las lecturas
multi-tenant. Cambiar a una org donde no hay Membership responde 404
(patron IDOR->404: no se revela la existencia de la org).
"""

from flask import Blueprint, request, jsonify

from app.schemas.members import SwitchWorkspaceSchema
from app.services.membership_service import MembershipService
from app.security import current_user, current_org_id, set_current_org, login_required

workspace_bp = Blueprint('workspace', __name__)


@workspace_bp.route('/api/workspace', methods=['GET'])
@login_required
def list_workspaces():
    return jsonify({
        'workspaces': MembershipService.workspaces(current_user(), current_org_id()),
    })


@workspace_bp.route('/api/workspace/switch', methods=['POST'])
@login_required
def switch_workspace():
    data = SwitchWorkspaceSchema(**(request.get_json(silent=True) or {}))
    membership = MembershipService.switch_workspace(current_user(), data.org_id)
    set_current_org(membership.org_id)
    return jsonify({'ok': True, 'org_id': membership.org_id, 'role': membership.role})

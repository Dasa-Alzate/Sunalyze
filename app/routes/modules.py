"""Marketplace de módulos de cara al usuario.

Solo lista módulos marcados is_visible. Activar/desactivar crea un override de
ámbito org (autoservicio sin pago por ahora); cuando exista billing, este punto
pasará por entitlement.
"""

from flask import Blueprint, jsonify

from app.services.flag_service import FlagService
from app.authz import require_permission, Permission
from app.security import current_org_id, current_user

modules_bp = Blueprint('modules', __name__)


@modules_bp.route('/api/modules', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_modules():
    user = current_user()
    return jsonify(FlagService.marketplace(current_org_id(), user.id))


@modules_bp.route('/api/modules/<key>/enable', methods=['POST'])
@require_permission(Permission.MODULE_MANAGE)
def enable_module(key):
    FlagService.enable_for_org(key, current_org_id(), created_by=current_user().id)
    return jsonify({'ok': True, 'enabled': True})


@modules_bp.route('/api/modules/<key>/disable', methods=['POST'])
@require_permission(Permission.MODULE_MANAGE)
def disable_module(key):
    FlagService.disable_for_org(key, current_org_id(), created_by=current_user().id)
    return jsonify({'ok': True, 'enabled': False})

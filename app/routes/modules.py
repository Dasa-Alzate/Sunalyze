
from flask import Blueprint, jsonify

from app.extensions import db
from app.models.flag import Flag
from app.services.flag_service import FlagService
from app.services.audit_service import AuditService
from app.authz import require_permission, Permission
from app.security import current_org_id, current_user

modules_bp = Blueprint('modules', __name__)


def _module_name(key):
    flag = Flag.query.filter_by(key=key).first()
    return flag.nombre if flag else key


@modules_bp.route('/api/modules', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_modules():
    user = current_user()
    return jsonify(FlagService.marketplace(current_org_id(), user.id))


@modules_bp.route('/api/modules/<key>/enable', methods=['POST'])
@require_permission(Permission.MODULE_MANAGE)
def enable_module(key):
    user = current_user()
    FlagService.enable_for_org(key, current_org_id(), created_by=user.id)
    AuditService.record(
        'module.enable', actor=user, org_id=current_org_id(),
        entity_type='module', entity_id=None,
        payload={'key': key, 'nombre': _module_name(key)},
    )
    db.session.commit()
    return jsonify({'ok': True, 'enabled': True})


@modules_bp.route('/api/modules/<key>/disable', methods=['POST'])
@require_permission(Permission.MODULE_MANAGE)
def disable_module(key):
    user = current_user()
    FlagService.disable_for_org(key, current_org_id(), created_by=user.id)
    AuditService.record(
        'module.disable', actor=user, org_id=current_org_id(),
        entity_type='module', entity_id=None,
        payload={'key': key, 'nombre': _module_name(key)},
    )
    db.session.commit()
    return jsonify({'ok': True, 'enabled': False})

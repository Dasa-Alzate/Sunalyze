"""Consola de plataforma: gestión de feature flags. Solo super-admin."""

from flask import Blueprint, request, jsonify

from app.schemas.flags import FlagSchema, OverrideSchema, ClearOverrideSchema
from app.services.flag_service import FlagService
from app.models.organization import Organization
from app.models.user import User
from app.superadmin.guards import require_superadmin
from app.security import current_user

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/flags', methods=['GET'])
@require_superadmin
def list_flags():
    return jsonify(FlagService.list_admin())


@admin_bp.route('/api/admin/flags', methods=['POST'])
@require_superadmin
def upsert_flag():
    data = FlagSchema(**(request.get_json(silent=True) or {}))
    flag = FlagService.upsert_flag(data.key, **data.model_dump(exclude={'key'}))
    return jsonify(flag.to_dict()), 201


@admin_bp.route('/api/admin/flags/<key>/override', methods=['POST'])
@require_superadmin
def set_override(key):
    data = OverrideSchema(**(request.get_json(silent=True) or {}))
    override = FlagService.set_override(
        key, data.scope, data.scope_id, data.enabled, created_by=current_user().id,
    )
    return jsonify(override.to_dict())


@admin_bp.route('/api/admin/flags/<key>/override', methods=['DELETE'])
@require_superadmin
def clear_override(key):
    data = ClearOverrideSchema(**(request.get_json(silent=True) or {}))
    FlagService.clear_override(key, data.scope, data.scope_id)
    return jsonify({'ok': True})


@admin_bp.route('/api/admin/organizations', methods=['GET'])
@require_superadmin
def list_orgs():
    orgs = Organization.query.order_by(Organization.nombre).all()
    return jsonify([{'id': o.id, 'nombre': o.nombre, 'type': o.type} for o in orgs])


@admin_bp.route('/api/admin/users', methods=['GET'])
@require_superadmin
def list_users():
    users = User.query.order_by(User.email).all()
    return jsonify([{'id': u.id, 'email': u.email, 'full_name': u.full_name} for u in users])

"""Endpoint de lectura de la bitacora de auditoria del workspace activo.

Capa HTTP fina sobre AuditService. Scoped al `org_id` activo y protegido por el
permiso `audit:view`.
"""

from flask import Blueprint, request, jsonify

from app.security import current_org_id
from app.authz import require_permission, Permission
from app.services.audit_service import AuditService

audit_bp = Blueprint('audit', __name__)

_MAX_LIMIT = 500


@audit_bp.route('/api/audit', methods=['GET'])
@require_permission(Permission.AUDIT_VIEW)
def list_audit():
    try:
        limit = int(request.args.get('limit', 100))
    except (TypeError, ValueError):
        limit = 100
    limit = max(1, min(limit, _MAX_LIMIT))
    events = AuditService.list_for_org(current_org_id(), limit=limit)
    return jsonify([e.to_dict() for e in events])

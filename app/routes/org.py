"""Endpoints de la organización. Capa HTTP fina.

El branding de la org (logo, color, pie) se aplica al render de documentos. Lectura y
escritura exigen ORG_MANAGE (owner+admin). El alcance es la org del workspace activo
(`current_org_id()`), 1:1 con la organización, sin IDOR por recurso.
"""

from flask import Blueprint, request, jsonify

from app.security import current_org_id
from app.authz import require_permission, Permission
from app.services.org_service import OrgService
from app.schemas.org import OrgBrandingSchema

org_bp = Blueprint('org', __name__)


def _body():
    return request.get_json(silent=True) or {}


@org_bp.route('/api/org/branding', methods=['GET'])
@require_permission(Permission.ORG_MANAGE)
def get_branding():
    return jsonify(OrgService.get_branding(current_org_id()))


@org_bp.route('/api/org/branding', methods=['PATCH'])
@require_permission(Permission.ORG_MANAGE)
def update_branding():
    data = OrgBrandingSchema(**_body())
    return jsonify(OrgService.update_branding(
        current_org_id(), data.model_dump(exclude_unset=True)))

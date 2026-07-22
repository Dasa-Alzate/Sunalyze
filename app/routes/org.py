"""Endpoints de la organización. Capa HTTP fina.

El branding de la org (logo, color, pie) se aplica al render de documentos. Lectura y
escritura exigen ORG_MANAGE (owner+admin). El alcance es la org del workspace activo
(`current_org_id()`), 1:1 con la organización, sin IDOR por recurso.
"""

from flask import Blueprint, request, jsonify, current_app, send_from_directory

from app.security import current_org_id
from app.authz import require_permission, Permission
from app.errors import ValidationError, NotFound
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


@org_bp.route('/api/org/branding/logo', methods=['POST'])
@require_permission(Permission.ORG_MANAGE)
def upload_logo():
    upload = request.files.get('logo') or next(iter(request.files.values()), None)
    if upload is None or not upload.filename:
        raise ValidationError('No se recibió ningún archivo de logo.')
    return jsonify(OrgService.save_logo(
        current_org_id(), current_app.instance_path, upload.read()))


@org_bp.route('/api/org/branding/logo', methods=['GET'])
@require_permission(Permission.ORG_MANAGE)
def get_logo():
    org_id = current_org_id()
    logo_path = OrgService.get_branding(org_id).get('logo_path')
    if not logo_path or not logo_path.startswith(f'cfiles/{org_id}/'):
        raise NotFound('La organización no tiene logo.')
    return send_from_directory(current_app.instance_path, logo_path)

"""CRUD e import de perfiles de consumo (org-scoped, con curados globales de solo lectura)."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from app.extensions import db
from app.authz import require_permission, Permission
from app.errors import NotFound, ValidationError
from app.models.consumption_profile import ConsumptionProfile
from app.schemas.consumption_profile import ConsumptionProfileCreateSchema, ConsumptionProfileUpdateSchema
from app.security import current_user, current_org_id
from app.services.audit_service import AuditService
from app.services.consumption import CDM_VERSION, build_fractions, parse_consumption_file
from app.services.consumption.expanders import ProfilePayloadError
from app.services.consumption.imports import ProfileImportError

IMPORT_MAX_BYTES = 4 * 1024 * 1024
IMPORT_ALLOWED_EXTENSIONS = {'csv', 'json'}

consumption_bp = Blueprint('consumption_profiles', __name__)


def _own_profile_or_404(profile_id):
    profile = ConsumptionProfile.active().filter_by(id=profile_id, org_id=current_org_id()).first()
    if profile is None:
        raise NotFound('Perfil de consumo no encontrado.')
    return profile


def _visible_profile_or_404(profile_id):
    profile = ConsumptionProfile.active().filter(
        ConsumptionProfile.id == profile_id,
        db.or_(ConsumptionProfile.org_id == current_org_id(), ConsumptionProfile.org_id.is_(None)),
    ).first()
    if profile is None:
        raise NotFound('Perfil de consumo no encontrado.')
    return profile


def _store(name, kind, payload, origin):
    try:
        fractions, hint = build_fractions(kind, payload)
    except ProfilePayloadError as err:
        raise ValidationError(str(err), code='profile.bad_payload') from err
    profile = ConsumptionProfile(
        org_id=current_org_id(), name=name, kind=kind, origin=origin,
        annual_kwh_hint=hint, cdm_version=CDM_VERSION,
    )
    profile.source = payload
    profile.fractions = fractions
    db.session.add(profile)
    db.session.flush()
    return profile


@consumption_bp.route('/api/consumption-profiles', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_profiles():
    profiles = ConsumptionProfile.active().filter(
        db.or_(ConsumptionProfile.org_id == current_org_id(), ConsumptionProfile.org_id.is_(None)),
    ).order_by(ConsumptionProfile.org_id.is_(None), ConsumptionProfile.name).all()
    return jsonify([p.to_dict() for p in profiles])


@consumption_bp.route('/api/consumption-profiles/<int:profile_id>', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def get_profile(profile_id):
    profile = _visible_profile_or_404(profile_id)
    return jsonify(profile.to_dict(include_source=True))


@consumption_bp.route('/api/consumption-profiles/<int:profile_id>/preview', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def preview_profile(profile_id):
    profile = _visible_profile_or_404(profile_id)
    fractions = profile.fractions or []
    hours = [0.0] * 24
    for i, value in enumerate(fractions):
        hours[i % 24] += value
    winter = [sum(fractions[d * 24 + h] for d in range(31)) for h in range(24)]
    summer = [sum(fractions[d * 24 + h] for d in range(181, 212)) for h in range(24)]
    return jsonify({
        'id': profile.id,
        'name': profile.name,
        'kind': profile.kind,
        'origin': profile.origin,
        'hours': hours,
        'winter': winter,
        'summer': summer,
        'annual_kwh_hint': profile.annual_kwh_hint,
    })


@consumption_bp.route('/api/consumption-profiles', methods=['POST'])
@require_permission(Permission.PROJECT_EDIT)
def create_profile():
    try:
        data = ConsumptionProfileCreateSchema(**(request.get_json(silent=True) or {}))
    except PydanticValidationError as err:
        raise ValidationError(err.errors()[0]['msg'], code='profile.invalid') from err
    profile = _store(data.name, data.kind, data.payload, 'ui')
    AuditService.record(
        'consumption_profile.create', actor=current_user(), org_id=current_org_id(),
        entity_type='consumption_profile', entity_id=profile.id,
        payload={'name': profile.name, 'kind': profile.kind},
    )
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@consumption_bp.route('/api/consumption-profiles/import', methods=['POST'])
@require_permission(Permission.PROJECT_EDIT)
def import_profile():
    uploaded = request.files.get('file')
    if uploaded is None or not uploaded.filename:
        raise ValidationError('Adjunta un archivo en el campo «file».', code='import.no_file')
    extension = uploaded.filename.rsplit('.', 1)[-1].lower() if '.' in uploaded.filename else ''
    if extension not in IMPORT_ALLOWED_EXTENSIONS:
        raise ValidationError('Formato no admitido. Usa CSV o JSON.', code='import.bad_extension')
    content = uploaded.read()
    if not content:
        raise ValidationError('El archivo está vacío.', code='import.empty')
    if len(content) > IMPORT_MAX_BYTES:
        raise ValidationError('El archivo supera el límite de 4 MB.', code='import.too_large')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = content.decode('latin-1')
    try:
        kind, payload = parse_consumption_file(uploaded.filename, text)
    except ProfileImportError as err:
        raise ValidationError(str(err), code='import.unreadable') from err
    name = (request.form.get('name') or '').strip() or uploaded.filename.rsplit('.', 1)[0][:150]
    profile = _store(name, kind, payload, 'file')
    AuditService.record(
        'consumption_profile.import', actor=current_user(), org_id=current_org_id(),
        entity_type='consumption_profile', entity_id=profile.id,
        payload={'name': profile.name, 'kind': profile.kind, 'filename': uploaded.filename},
    )
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@consumption_bp.route('/api/consumption-profiles/<int:profile_id>', methods=['PATCH'])
@require_permission(Permission.PROJECT_EDIT)
def update_profile(profile_id):
    profile = _own_profile_or_404(profile_id)
    try:
        data = ConsumptionProfileUpdateSchema(**(request.get_json(silent=True) or {}))
    except PydanticValidationError as err:
        raise ValidationError(err.errors()[0]['msg'], code='profile.invalid') from err
    if data.name:
        profile.name = data.name
    db.session.commit()
    return jsonify(profile.to_dict())


@consumption_bp.route('/api/consumption-profiles/<int:profile_id>', methods=['DELETE'])
@require_permission(Permission.PROJECT_EDIT)
def delete_profile(profile_id):
    profile = _own_profile_or_404(profile_id)
    profile.soft_delete()
    AuditService.record(
        'consumption_profile.delete', actor=current_user(), org_id=current_org_id(),
        entity_type='consumption_profile', entity_id=profile.id,
        payload={'name': profile.name},
    )
    db.session.commit()
    return jsonify({'deleted': True})

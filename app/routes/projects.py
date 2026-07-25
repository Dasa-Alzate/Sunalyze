
import logging
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project, ESTADOS
from app.security import current_org_id, current_user
from app.authz import require_permission, Permission
from app.errors import NotFound, ValidationError
from app.services.audit_service import AuditService
from app.services.catalog_service import CatalogService
from app.services.org_service import OrgService
from app.models.battery import Battery
from app.schemas.project import ProjectCreateSchema, ProjectUpdateSchema

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)

_EDITABLE_FIELDS = [
    'cliente', 'direccion', 'localidad',
    'latitud', 'longitud', 'necesidad', 'autoconsumo',
    'coplanar', 'inclinacion', 'azimut',
    'panel_id', 'inverter_id',
    'battery_id', 'battery_quantity',
    'referencia_catastral', 'cups', 'compania',
    'potencia_contratada', 'tipo_voltaje', 'ccaa',
]


def _validate_battery(data, org_id):
    if 'battery_id' not in data:
        return
    battery_id = data.get('battery_id')
    if battery_id in (None, ''):
        return
    battery = Battery.query.get(battery_id)
    visible = CatalogService.visible_catalog_ids(org_id)
    if not battery or battery.catalog_id not in visible:
        raise NotFound('Bateria no encontrada', code='battery.not_found')


def _apply(project, data):
    for field in _EDITABLE_FIELDS:
        if field in data:
            setattr(project, field, data[field])
    if 'resultados' in data:
        project.resultados = data['resultados']


def _owned_or_404(project_id, include_deleted=False):
    org_id = current_org_id()
    project = Project.query.get(project_id)
    if not project or project.org_id != org_id:
        raise NotFound('Proyecto no encontrado.', code='project.not_found')
    if project.is_deleted and not include_deleted:
        raise NotFound('Proyecto no encontrado.', code='project.not_found')
    return project


def _wants_deleted():
    return request.args.get('deleted', '').lower() in ('1', 'true', 'yes')


@projects_bp.route('/api/projects', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_projects():
    if _wants_deleted():
        return list_deleted_projects()
    estado = request.args.get('estado')
    query = Project.query.filter(
        Project.org_id == current_org_id(),
        Project.deleted_at.is_(None),
    )
    if estado and estado != 'todos':
        query = query.filter(Project.estado == estado)
    projects = query.order_by(Project.updated_at.desc()).all()
    prefix = OrgService.get_branding(current_org_id()).get('project_prefix')
    return jsonify([p.to_dict(prefix=prefix) for p in projects])


@require_permission(Permission.PROJECT_DELETE)
def list_deleted_projects():
    projects = (
        Project.query.filter(
            Project.org_id == current_org_id(),
            Project.deleted_at.isnot(None),
        )
        .order_by(Project.deleted_at.desc())
        .all()
    )
    prefix = OrgService.get_branding(current_org_id()).get('project_prefix')
    return jsonify([p.to_dict(prefix=prefix) for p in projects])


@projects_bp.route('/api/projects/<int:project_id>', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def get_project(project_id):
    return jsonify(_owned_or_404(project_id).to_dict())


@projects_bp.route('/api/projects', methods=['POST'])
@require_permission(Permission.PROJECT_CREATE)
def create_project():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    if data.get('estado') and data['estado'] not in ESTADOS:
        raise ValidationError(f"Estado invalido. Validos: {', '.join(ESTADOS)}", code='project.invalid_estado')

    clean = ProjectCreateSchema(**data).model_dump(exclude_unset=True)
    _validate_battery(clean, current_org_id())
    project = Project(cliente=clean['cliente'], org_id=current_org_id())
    project.serial_seq = Project.next_serial_seq(current_org_id())
    _apply(project, clean)
    db.session.add(project)
    db.session.flush()
    AuditService.record(
        'project.create', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente},
    )
    db.session.commit()
    return jsonify(project.to_dict()), 201


@projects_bp.route('/api/projects/<int:project_id>', methods=['PATCH'])
@require_permission(Permission.PROJECT_EDIT)
def update_project(project_id):
    project = _owned_or_404(project_id)
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    if data.get('estado') and data['estado'] not in ESTADOS:
        raise ValidationError(f"Estado invalido. Validos: {', '.join(ESTADOS)}", code='project.invalid_estado')
    clean = ProjectUpdateSchema(**data).model_dump(exclude_unset=True)
    _validate_battery(clean, current_org_id())
    changed = sorted(
        f for f in _EDITABLE_FIELDS
        if f in clean and clean[f] != getattr(project, f)
    )
    _apply(project, clean)
    AuditService.record(
        'project.update', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'changed_fields': changed},
    )
    db.session.commit()
    return jsonify(project.to_dict())


@projects_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@require_permission(Permission.PROJECT_DELETE)
def delete_project(project_id):
    project = _owned_or_404(project_id)
    project.soft_delete()
    AuditService.record(
        'project.delete', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente},
    )
    db.session.commit()
    return jsonify({'message': 'Proyecto eliminado correctamente'})


@projects_bp.route('/api/projects/<int:project_id>/restore', methods=['POST'])
@require_permission(Permission.PROJECT_DELETE)
def restore_project(project_id):
    project = _owned_or_404(project_id, include_deleted=True)
    project.deleted_at = None
    AuditService.record(
        'project.restore', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente},
    )
    db.session.commit()
    return jsonify(project.to_dict())


@projects_bp.route('/api/projects/<int:project_id>/duplicate', methods=['POST'])
@require_permission(Permission.PROJECT_CREATE)
def duplicate_project(project_id):
    source = _owned_or_404(project_id)
    clone = Project(cliente=f'{source.cliente} (copia)', org_id=current_org_id())
    clone.serial_seq = Project.next_serial_seq(current_org_id())
    copied = {f: getattr(source, f) for f in _EDITABLE_FIELDS if f not in ('cliente', 'estado')}
    _apply(clone, copied)
    clone.resultados = source.resultados
    clone.estado = 'borrador'
    db.session.add(clone)
    db.session.commit()
    return jsonify(clone.to_dict()), 201

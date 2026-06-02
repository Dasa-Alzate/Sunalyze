"""CRUD de proyectos, scoped al workspace (org) activo del usuario."""

import logging
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project, ESTADOS
from app.security import current_org_id, current_user
from app.authz import require_permission, Permission
from app.errors import NotFound, ValidationError
from app.services.audit_service import AuditService
from app.services.catalog_service import CatalogService
from app.models.battery import Battery

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)

_EDITABLE_FIELDS = [
    'cliente', 'direccion', 'localidad',
    'latitud', 'longitud', 'necesidad', 'autoconsumo',
    'coplanar', 'inclinacion', 'azimut',
    'panel_id', 'inverter_id',
    'battery_id', 'battery_quantity',
    'referencia_catastral', 'cups', 'compania',
    'potencia_contratada', 'tipo_voltaje',
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


def _owned_or_404(project_id):
    org_id = current_org_id()
    project = Project.query.get(project_id)
    if not project or project.org_id != org_id:
        raise NotFound('Proyecto no encontrado.', code='project.not_found')
    return project


@projects_bp.route('/api/projects', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_projects():
    estado = request.args.get('estado')
    query = Project.query.filter(Project.org_id == current_org_id())
    if estado and estado != 'todos':
        query = query.filter(Project.estado == estado)
    projects = query.order_by(Project.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


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
    if not data.get('cliente'):
        raise ValidationError('Campo requerido: cliente.', code='project.cliente_required')
    if data.get('estado') and data['estado'] not in ESTADOS:
        raise ValidationError(f"Estado invalido. Validos: {', '.join(ESTADOS)}", code='project.invalid_estado')

    _validate_battery(data, current_org_id())
    project = Project(cliente=data['cliente'], org_id=current_org_id())
    _apply(project, data)
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
    _validate_battery(data, current_org_id())
    changed = sorted(
        f for f in _EDITABLE_FIELDS
        if f in data and data[f] != getattr(project, f)
    )
    _apply(project, data)
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
    AuditService.record(
        'project.delete', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente},
    )
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Proyecto eliminado correctamente'})


@projects_bp.route('/api/projects/<int:project_id>/duplicate', methods=['POST'])
@require_permission(Permission.PROJECT_CREATE)
def duplicate_project(project_id):
    source = _owned_or_404(project_id)
    clone = Project(cliente=f'{source.cliente} (copia)', org_id=current_org_id())
    copied = {f: getattr(source, f) for f in _EDITABLE_FIELDS if f not in ('cliente', 'estado')}
    _apply(clone, copied)
    clone.resultados = source.resultados
    clone.estado = 'borrador'
    db.session.add(clone)
    db.session.commit()
    return jsonify(clone.to_dict()), 201

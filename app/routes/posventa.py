
from flask import Blueprint, request, jsonify

from app.models.installation import (
    Installation, MaintenanceVisit, Incident, ProductionReading,
)
from app.services.installation_service import InstallationService
from app.security import current_org_id
from app.authz import require_permission, require_flag, Permission
from app.errors import NotFound, ValidationError

posventa_bp = Blueprint('posventa', __name__)


def _installation_or_404(installation_id):
    org_id = current_org_id()
    installation = Installation.query.get(installation_id)
    if not installation or installation.org_id != org_id:
        raise NotFound('Instalacion no encontrada.', code='installation.not_found')
    return installation


def _child_or_404(model, child_id, installation):
    child = model.query.get(child_id)
    if not child or child.installation_id != installation.id:
        raise NotFound('Recurso no encontrado.', code='error.not_found')
    return child


def _body():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    return data


@posventa_bp.route('/api/installations', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def list_installations():
    installations = (
        Installation.query
        .filter(Installation.org_id == current_org_id())
        .order_by(Installation.updated_at.desc())
        .all()
    )
    return jsonify([i.to_dict() for i in installations])


@posventa_bp.route('/api/installations', methods=['POST'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def create_installation():
    data = _body()
    if data.get('project_id') in (None, ''):
        raise ValidationError('Campo requerido: project_id.', code='posventa.project_id_required')
    installation = InstallationService.create_from_project(current_org_id(), data['project_id'])
    return jsonify(installation.to_dict()), 201


@posventa_bp.route('/api/installations/<int:installation_id>', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def get_installation(installation_id):
    installation = _installation_or_404(installation_id)
    body = installation.to_dict()
    body['performance'] = InstallationService.performance_summary(installation)
    body['maintenance'] = [v.to_dict() for v in installation.maintenance_visits]
    body['incidents'] = [i.to_dict() for i in installation.incidents]
    body['readings'] = [r.to_dict() for r in installation.readings]
    return jsonify(body)


@posventa_bp.route('/api/installations/<int:installation_id>', methods=['PATCH'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def update_installation(installation_id):
    installation = _installation_or_404(installation_id)
    installation = InstallationService.update_installation(installation, _body())
    return jsonify(installation.to_dict())


@posventa_bp.route('/api/installations/<int:installation_id>/performance', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def get_performance(installation_id):
    installation = _installation_or_404(installation_id)
    return jsonify(InstallationService.performance_summary(installation))


@posventa_bp.route('/api/installations/<int:installation_id>/maintenance', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def list_maintenance(installation_id):
    installation = _installation_or_404(installation_id)
    return jsonify([v.to_dict() for v in installation.maintenance_visits])


@posventa_bp.route('/api/installations/<int:installation_id>/maintenance', methods=['POST'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def create_maintenance(installation_id):
    installation = _installation_or_404(installation_id)
    visit = InstallationService.add_visit(installation, _body())
    return jsonify(visit.to_dict()), 201


@posventa_bp.route('/api/installations/<int:installation_id>/maintenance/<int:visit_id>', methods=['PATCH'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def update_maintenance(installation_id, visit_id):
    installation = _installation_or_404(installation_id)
    visit = _child_or_404(MaintenanceVisit, visit_id, installation)
    visit = InstallationService.update_visit(visit, _body())
    return jsonify(visit.to_dict())


@posventa_bp.route('/api/installations/<int:installation_id>/maintenance/<int:visit_id>', methods=['DELETE'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def delete_maintenance(installation_id, visit_id):
    installation = _installation_or_404(installation_id)
    visit = _child_or_404(MaintenanceVisit, visit_id, installation)
    InstallationService.delete(visit)
    return jsonify({'message': 'Visita eliminada correctamente'})


@posventa_bp.route('/api/installations/<int:installation_id>/incidents', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def list_incidents(installation_id):
    installation = _installation_or_404(installation_id)
    return jsonify([i.to_dict() for i in installation.incidents])


@posventa_bp.route('/api/installations/<int:installation_id>/incidents', methods=['POST'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def create_incident(installation_id):
    installation = _installation_or_404(installation_id)
    incident = InstallationService.add_incident(installation, _body())
    return jsonify(incident.to_dict()), 201


@posventa_bp.route('/api/installations/<int:installation_id>/incidents/<int:incident_id>', methods=['PATCH'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def update_incident(installation_id, incident_id):
    installation = _installation_or_404(installation_id)
    incident = _child_or_404(Incident, incident_id, installation)
    incident = InstallationService.update_incident(incident, _body())
    return jsonify(incident.to_dict())


@posventa_bp.route('/api/installations/<int:installation_id>/incidents/<int:incident_id>', methods=['DELETE'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def delete_incident(installation_id, incident_id):
    installation = _installation_or_404(installation_id)
    incident = _child_or_404(Incident, incident_id, installation)
    InstallationService.delete(incident)
    return jsonify({'message': 'Incidencia eliminada correctamente'})


@posventa_bp.route('/api/installations/<int:installation_id>/readings', methods=['GET'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_VIEW)
def list_readings(installation_id):
    installation = _installation_or_404(installation_id)
    return jsonify([r.to_dict() for r in installation.readings])


@posventa_bp.route('/api/installations/<int:installation_id>/readings', methods=['POST'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def create_reading(installation_id):
    installation = _installation_or_404(installation_id)
    reading = InstallationService.add_reading(installation, _body())
    return jsonify(reading.to_dict()), 201


@posventa_bp.route('/api/installations/<int:installation_id>/readings/<int:reading_id>', methods=['PATCH'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def update_reading(installation_id, reading_id):
    installation = _installation_or_404(installation_id)
    reading = _child_or_404(ProductionReading, reading_id, installation)
    reading = InstallationService.update_reading(reading, _body())
    return jsonify(reading.to_dict())


@posventa_bp.route('/api/installations/<int:installation_id>/readings/<int:reading_id>', methods=['DELETE'])
@require_flag('posventa')
@require_permission(Permission.PROJECT_EDIT)
def delete_reading(installation_id, reading_id):
    installation = _installation_or_404(installation_id)
    reading = _child_or_404(ProductionReading, reading_id, installation)
    InstallationService.delete(reading)
    return jsonify({'message': 'Lectura eliminada correctamente'})

"""Análisis económico horario del proyecto: factura, aporte de batería y escenarios."""

from flask import Blueprint, jsonify, request

from app.authz import require_permission, Permission
from app.errors import NotFound
from app.models.battery import Battery
from app.routes.projects import _owned_or_404
from app.services.catalog_service import CatalogService
from app.services.economics import EconomicsService
from app.security import current_org_id

economics_bp = Blueprint('economics', __name__)


def _battery_or_404(battery_id, org_id):
    battery = Battery.query.get(battery_id)
    visible = CatalogService.visible_catalog_ids(org_id)
    if not battery or battery.catalog_id not in visible:
        raise NotFound('Bateria no encontrada', code='battery.not_found')
    return battery


@economics_bp.route('/api/projects/<int:project_id>/economics', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
def compute_economics(project_id):
    project = _owned_or_404(project_id)
    data = request.get_json(silent=True) or {}
    battery = None
    quantity = 1
    battery_id = data.get('battery_id', project.battery_id)
    if battery_id:
        battery = _battery_or_404(battery_id, current_org_id())
        quantity = data.get('battery_quantity', project.battery_quantity) or 1
    return jsonify(EconomicsService.compute(project, current_org_id(), battery, quantity))


@economics_bp.route('/api/projects/<int:project_id>/economics/sweep', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
def economics_sweep(project_id):
    project = _owned_or_404(project_id)
    visible = CatalogService.visible_catalog_ids(current_org_id())
    batteries = (
        Battery.query.filter(Battery.catalog_id.in_(visible))
        .order_by(Battery.capacity_kwh)
        .limit(20)
        .all()
    )
    return jsonify(EconomicsService.sweep(project, current_org_id(), batteries))


@economics_bp.route('/api/projects/<int:project_id>/economics/scenarios', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
def economics_scenarios(project_id):
    project = _owned_or_404(project_id)
    visible = CatalogService.visible_catalog_ids(current_org_id())
    batteries = (
        Battery.query.filter(Battery.catalog_id.in_(visible))
        .order_by(Battery.capacity_kwh)
        .limit(20)
        .all()
    )
    return jsonify(EconomicsService.scenarios(project, current_org_id(), batteries))

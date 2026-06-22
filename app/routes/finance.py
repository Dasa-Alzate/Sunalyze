"""Endpoints del módulo financiero. Capa HTTP fina.

Todas las rutas van detrás del flag `finance` (@require_flag) y de un permiso RBAC
(lectura: PROJECT_VIEW; escritura: PROJECT_EDIT). El alcance por org_id se aplica en
FinanceService (IDOR -> 404). `compute` calcula al vuelo sin persistir; los escenarios
son el CRUD persistente por proyecto.
"""

from flask import Blueprint, request, jsonify

from app.security import current_org_id, current_user
from app.authz import require_permission, require_flag, Permission
from app.services.finance_service import FinanceService
from app.schemas.finance import ComputeRequest, ScenarioCreate, ScenarioUpdate

finance_bp = Blueprint('finance', __name__)

FLAG = 'finance'


def _body():
    return request.get_json(silent=True) or {}


@finance_bp.route('/api/projects/<int:project_id>/financial/compute', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_VIEW)
def compute_financial(project_id):
    data = ComputeRequest(**_body())
    result = FinanceService.compute_for_project(
        current_org_id(), project_id, data.assumptions,
        production_kwh_year=data.production_kwh_year,
        self_consumption_ratio=data.self_consumption_ratio,
    )
    return jsonify(result)


@finance_bp.route('/api/projects/<int:project_id>/financial/scenarios', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_VIEW)
def list_scenarios(project_id):
    return jsonify(FinanceService.list_scenarios(current_org_id(), project_id))


@finance_bp.route('/api/projects/<int:project_id>/financial/scenarios', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_EDIT)
def create_scenario(project_id):
    data = ScenarioCreate(**_body())
    user = current_user()
    scenario = FinanceService.create_scenario(
        current_org_id(), project_id, data, created_by=user.id if user else None)
    return jsonify(scenario.to_dict()), 201


@finance_bp.route('/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_VIEW)
def get_scenario(project_id, scenario_id):
    return jsonify(FinanceService.get_scenario(current_org_id(), project_id, scenario_id).to_dict())


@finance_bp.route('/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>', methods=['PATCH'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_EDIT)
def update_scenario(project_id, scenario_id):
    data = ScenarioUpdate(**_body())
    scenario = FinanceService.update_scenario(current_org_id(), project_id, scenario_id, data)
    return jsonify(scenario.to_dict())


@finance_bp.route('/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>', methods=['DELETE'])
@require_flag(FLAG)
@require_permission(Permission.PROJECT_EDIT)
def delete_scenario(project_id, scenario_id):
    FinanceService.delete_scenario(current_org_id(), project_id, scenario_id)
    return jsonify({'ok': True})

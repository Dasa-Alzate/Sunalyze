from flask import Blueprint, jsonify, request

from app.extensions import db
from app.authz import require_permission, Permission
from app.schemas.budget import BudgetPayloadSchema
from app.security import current_user, current_org_id
from app.services.audit_service import AuditService
from app.services.budget_service import BudgetService
from app.routes.projects import _owned_or_404

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/api/projects/<int:project_id>/budget', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def get_budget(project_id):
    project = _owned_or_404(project_id)
    return jsonify(BudgetService.get_budget(project))


@budget_bp.route('/api/projects/<int:project_id>/budget', methods=['PUT'])
@require_permission(Permission.PROJECT_EDIT)
def update_budget(project_id):
    project = _owned_or_404(project_id)
    payload = BudgetPayloadSchema(**(request.get_json(silent=True) or {}))
    result = BudgetService.replace(project, payload.iva_pct, [i.model_dump() for i in payload.items])
    AuditService.record(
        'budget.update', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente, 'total': result['totales']['total']},
    )
    db.session.commit()
    return jsonify(result)


@budget_bp.route('/api/projects/<int:project_id>/budget/seed', methods=['POST'])
@require_permission(Permission.PROJECT_EDIT)
def seed_budget(project_id):
    project = _owned_or_404(project_id)
    result = BudgetService.seed_from_design(project)
    AuditService.record(
        'budget.update', actor=current_user(), org_id=current_org_id(),
        entity_type='project', entity_id=project.id,
        payload={'cliente': project.cliente, 'seeded': True},
    )
    db.session.commit()
    return jsonify(result)

"""CRUD de planes eléctricos de comercializadora (org-scoped, con globales de solo lectura)."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from app.extensions import db
from app.authz import require_permission, Permission
from app.errors import NotFound, ValidationError
from app.models.electricity_plan import ElectricityPlan
from app.schemas.electricity_plan import ElectricityPlanCreateSchema, ElectricityPlanUpdateSchema
from app.security import current_user, current_org_id
from app.services.audit_service import AuditService

electricity_plans_bp = Blueprint('electricity_plans', __name__)


def _own_plan_or_404(plan_id):
    plan = ElectricityPlan.active().filter_by(id=plan_id, org_id=current_org_id()).first()
    if plan is None:
        raise NotFound('Plan eléctrico no encontrado.', code='electricity_plan.not_found')
    return plan


def _parse(schema):
    try:
        return schema(**(request.get_json(silent=True) or {}))
    except PydanticValidationError as err:
        raise ValidationError(err.errors()[0]['msg'], code='electricity_plan.invalid') from err


@electricity_plans_bp.route('/api/electricity-plans', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def list_plans():
    plans = ElectricityPlan.active().filter(
        db.or_(ElectricityPlan.org_id == current_org_id(), ElectricityPlan.org_id.is_(None)),
    ).order_by(ElectricityPlan.org_id.is_(None), ElectricityPlan.comercializadora, ElectricityPlan.nombre).all()
    return jsonify([p.to_dict() for p in plans])


@electricity_plans_bp.route('/api/electricity-plans', methods=['POST'])
@require_permission(Permission.EQUIPMENT_EDIT)
def create_plan():
    data = _parse(ElectricityPlanCreateSchema)
    plan = ElectricityPlan(org_id=current_org_id(), **data.model_dump(exclude_none=True))
    db.session.add(plan)
    db.session.flush()
    AuditService.record(
        'electricity_plan.create', actor=current_user(), org_id=current_org_id(),
        entity_type='electricity_plan', entity_id=plan.id,
        payload={'comercializadora': plan.comercializadora, 'nombre': plan.nombre},
    )
    db.session.commit()
    return jsonify(plan.to_dict()), 201


@electricity_plans_bp.route('/api/electricity-plans/<int:plan_id>', methods=['PATCH'])
@require_permission(Permission.EQUIPMENT_EDIT)
def update_plan(plan_id):
    plan = _own_plan_or_404(plan_id)
    data = _parse(ElectricityPlanUpdateSchema)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(plan, field, value)
    db.session.commit()
    return jsonify(plan.to_dict())


@electricity_plans_bp.route('/api/electricity-plans/<int:plan_id>', methods=['DELETE'])
@require_permission(Permission.EQUIPMENT_EDIT)
def delete_plan(plan_id):
    plan = _own_plan_or_404(plan_id)
    plan.soft_delete()
    AuditService.record(
        'electricity_plan.delete', actor=current_user(), org_id=current_org_id(),
        entity_type='electricity_plan', entity_id=plan.id,
        payload={'comercializadora': plan.comercializadora, 'nombre': plan.nombre},
    )
    db.session.commit()
    return jsonify({'deleted': True})

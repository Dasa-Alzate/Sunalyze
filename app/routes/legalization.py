
from flask import Blueprint, request, jsonify

from app.models.project import Project
from app.schemas.legalization import TransitionSchema, SignMemoriaSchema
from app.services.legalization_service import LegalizationService
from app.security import current_user, current_org_id
from app.authz import require_permission, Permission
from app.errors import NotFound

legalization_bp = Blueprint('legalization', __name__)


def _owned_or_404(project_id):
    org_id = current_org_id()
    project = Project.query.get(project_id)
    if not project or project.org_id != org_id:
        raise NotFound('Proyecto no encontrado.', code='project.not_found')
    return project


@legalization_bp.route('/api/projects/<int:project_id>/legalization', methods=['GET'])
@require_permission(Permission.PROJECT_VIEW)
def get_legalization(project_id):
    project = _owned_or_404(project_id)
    summary = LegalizationService.state_summary(project)
    summary['historial'] = LegalizationService.history(project)
    return jsonify(summary)


@legalization_bp.route('/api/projects/<int:project_id>/legalization/transition', methods=['POST'])
@require_permission(Permission.PROJECT_LEGALIZE)
def transition(project_id):
    project = _owned_or_404(project_id)
    data = TransitionSchema(**(request.get_json(silent=True) or {}))
    LegalizationService.transition(project, current_user(), data.to_estado, data.note)
    return jsonify(LegalizationService.state_summary(project))


@legalization_bp.route('/api/projects/<int:project_id>/memoria/sign', methods=['POST'])
@require_permission(Permission.MEMORIA_SIGN)
def sign_memoria(project_id):
    project = _owned_or_404(project_id)
    data = SignMemoriaSchema(**(request.get_json(silent=True) or {}))
    signature = LegalizationService.sign_memoria(
        project, current_user(), data.pdf_sha256, data.pdf_size_bytes, data.note,
    )
    return jsonify(signature.to_dict()), 201

"""Endpoints de analisis, diagrama funcional y memoria PDF. HTTP fino sobre services."""

from flask import Blueprint, request, jsonify, render_template, Response

from app.services.analysis_service import AnalysisService
from app.services.diagrama_service import DiagramaService
from app.services.memoria_service import MemoriaService
from app.services.catalog_service import CatalogService
from app.schemas.memoria import MemoriaFormSchema
from app.security import current_org_id
from app.authz import require_permission, Permission
from app.errors import ValidationError

bp = Blueprint('main', __name__)


@bp.route('/api/panel-analysis', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
def panel_analysis():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    visible = CatalogService.visible_catalog_ids(current_org_id())
    result = AnalysisService.calculate(data, visible)
    return jsonify(result)


@bp.route('/api/diagrama-completo', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
def diagrama_completo():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    template_vars = DiagramaService.build_template_vars(data)
    return render_template('diagrama_funcional.html', **template_vars)


@bp.route('/imprimir/memoria-pdf', methods=['GET', 'POST'])
@require_permission(Permission.MEMORIA_SIGN)
def generar_memoria_pdf():
    if request.method == 'POST':
        MemoriaFormSchema(**request.form.to_dict())
    pdf = MemoriaService.generar_pdf(request.form if request.method == 'POST' else {})
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'inline; filename=memoria_tecnica.pdf'},
    )

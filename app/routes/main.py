"""Endpoints de analisis, diagrama funcional y memoria PDF. HTTP fino sobre services."""

from flask import Blueprint, request, jsonify, render_template, Response, current_app

from app.extensions import limiter
from app.services.analysis_service import AnalysisService
from app.services.diagrama_service import DiagramaService
from app.services.catalog_service import CatalogService
from app.schemas.memoria import MemoriaFormSchema
from app.security import current_org_id, current_user
from app.authz import require_permission, Permission
from app.errors import ValidationError, NotFound
from app.gateways.queue import get_queue, STATUS_FINISHED, STATUS_FAILED

bp = Blueprint('main', __name__)


def _pdf_ratelimit():
    return current_app.config.get('PDF_RATELIMIT', '60 per hour')


def _analysis_ratelimit():
    return current_app.config.get('ANALYSIS_RATELIMIT', '120 per hour')


@bp.route('/api/panel-analysis', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
@limiter.limit(_analysis_ratelimit)
def panel_analysis():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    visible = CatalogService.visible_catalog_ids(current_org_id())
    result = AnalysisService.calculate(data, visible)
    return jsonify(result)


@bp.route('/api/diagrama-completo', methods=['POST'])
@require_permission(Permission.PROJECT_VIEW)
@limiter.limit(_analysis_ratelimit)
def diagrama_completo():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError('Cuerpo JSON requerido.', code='request.body_required')
    template_vars = DiagramaService.build_template_vars(data)
    return render_template('diagrama_funcional.html', **template_vars)


def _memoria_pdf_response(pdf):
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'inline; filename=memoria_tecnica.pdf'},
    )


@bp.route('/imprimir/memoria-pdf', methods=['GET', 'POST'])
@require_permission(Permission.MEMORIA_SIGN)
@limiter.limit(_pdf_ratelimit)
def generar_memoria_pdf():
    form_data = request.form.to_dict() if request.method == 'POST' else {}
    if request.method == 'POST':
        MemoriaFormSchema(**form_data)
    queue = get_queue()
    user = current_user()
    job_id = queue.enqueue(
        'memoria_pdf', form_data=form_data,
        org_id=current_org_id(), user_id=user.id if user else None,
    )
    if queue.is_async:
        return jsonify({'job_id': job_id, 'status': queue.get_status(job_id)}), 202
    return _memoria_pdf_response(queue.get_result(job_id)['pdf'])


@bp.route('/imprimir/memoria-pdf/jobs/<job_id>', methods=['GET'])
@require_permission(Permission.MEMORIA_SIGN)
def memoria_pdf_job_status(job_id):
    queue = get_queue()
    status = queue.get_status(job_id)
    if status == STATUS_FINISHED:
        result = queue.get_result(job_id)
        if not result or result.get('pdf') is None:
            raise NotFound('Resultado del trabajo no disponible.')
        if result.get('org_id') != current_org_id():
            raise NotFound('Trabajo no encontrado.')
        return _memoria_pdf_response(result['pdf'])
    if status == STATUS_FAILED:
        return jsonify({'job_id': job_id, 'status': status}), 500
    return jsonify({'job_id': job_id, 'status': status}), 202

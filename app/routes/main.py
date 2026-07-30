
from flask import Blueprint, request, jsonify, render_template, Response, current_app

from app.extensions import limiter, db
from app.services.analysis_service import AnalysisService
from app.services.diagrama_service import DiagramaService
from app.services.catalog_service import CatalogService
from app.schemas.memoria import MemoriaFormSchema
from app.security import current_org_id, current_user
from app.authz import require_permission, Permission
from app.errors import ValidationError, NotFound
from app.gateways.queue import get_queue, STATUS_FINISHED, STATUS_FAILED
from app.services.audit_service import AuditService

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


@bp.route('/imprimir/memoria-preview', methods=['POST'])
@require_permission(Permission.EQUIPMENT_VIEW)
def memoria_preview():
    from app.services.memoria_service import MemoriaService
    raw = request.get_json(silent=True) or {}
    form_data = {str(k): str(v) for k, v in raw.items() if v is not None}
    html = MemoriaService.preview_html(form_data, org_id=current_org_id())
    return Response(html, mimetype='text/html')


def _bill_kwargs():
    from app.models.organization import Organization
    raw = request.get_json(silent=True) or {}

    def num(key, default=None):
        try:
            return float(raw[key])
        except (KeyError, TypeError, ValueError):
            return default

    consumption = num('consumption_kwh')
    production = num('production_kwh')
    if not consumption or not production:
        raise ValidationError('Indica consumption_kwh y production_kwh.')
    org_id = current_org_id()
    org = Organization.query.get(org_id) if org_id else None
    return {
        'consumption_kwh': consumption,
        'production_kwh': production,
        'tariff': num('tariff', 0.15),
        'surplus_price': num('surplus_price', 0.06),
        'self_consumption_ratio': num('self_consumption_ratio', 0.65),
        'fixed_cost_year': num('fixed_cost_year', 0.0),
        'escalation': num('tariff_escalation_pct', 0.025),
        'lifetime_years': int(num('lifetime_years', 25)),
        'installed_kwp': num('installed_kwp'),
        'client': raw.get('client'),
        'project_name': raw.get('project_name'),
        'org_name': getattr(org, 'nombre', None),
    }


@bp.route('/imprimir/recibo-comparativo', methods=['POST'])
@require_permission(Permission.EQUIPMENT_VIEW)
def recibo_comparativo():
    from app.services.energy_bill_service import EnergyBillService
    return Response(EnergyBillService.render_html(**_bill_kwargs()), mimetype='text/html')


@bp.route('/imprimir/recibo-comparativo.pdf', methods=['POST'])
@require_permission(Permission.EQUIPMENT_VIEW)
@limiter.limit(_pdf_ratelimit)
def recibo_comparativo_pdf():
    from weasyprint import HTML
    from app.services.energy_bill_service import EnergyBillService
    html = EnergyBillService.render_html(**_bill_kwargs())
    pdf = HTML(string=html, base_url=request.url_root).write_pdf()
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': 'inline; filename="comparativa-factura.pdf"'})


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
    AuditService.record(
        'memoria.generate', actor=user, org_id=current_org_id(),
        entity_type='memoria', entity_id=None,
    )
    db.session.commit()
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

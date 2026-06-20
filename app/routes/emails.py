"""Endpoints de plantillas de correo: catalogo, preview y envio (dev)."""

import logging
from flask import Blueprint, request, jsonify, Response
from app.services.email_service import EmailService
from app.security import login_required
from app.extensions import limiter
from app.superadmin.guards import is_superadmin
from app.errors import Forbidden, NotFound, ValidationError

logger = logging.getLogger(__name__)

emails_bp = Blueprint('emails', __name__)


@emails_bp.route('/api/emails', methods=['GET'])
@login_required
def list_emails():
    return jsonify(EmailService.catalog())


@emails_bp.route('/api/emails/<template_id>/preview', methods=['GET'])
@login_required
def preview_email(template_id):
    try:
        context = request.args.to_dict()
        rendered = EmailService.render(template_id, context)
    except KeyError:
        raise NotFound(f'Plantilla desconocida: {template_id}', code='email.template_not_found')
    return Response(rendered['html'], mimetype='text/html')


@emails_bp.route('/api/emails/<template_id>/send', methods=['POST'])
@login_required
@limiter.limit('10 per hour')
def send_email(template_id):
    if not is_superadmin():
        raise Forbidden('Solo un superadmin puede enviar correos.', code='auth.superadmin_required')
    data = request.get_json(silent=True) or {}
    to = data.get('to')
    if not to:
        raise ValidationError("Campo requerido: 'to'.", code='email.to_required')
    try:
        result = EmailService.send(template_id, to, data.get('context'))
    except KeyError:
        raise NotFound(f'Plantilla desconocida: {template_id}', code='email.template_not_found')
    return jsonify(result)

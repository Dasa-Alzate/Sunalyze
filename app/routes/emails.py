"""Endpoints de plantillas de correo: catalogo, preview y envio (dev)."""

import logging
from flask import Blueprint, request, jsonify, Response
from app.services.email_service import EmailService
from app.security import login_required

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
        return jsonify({'error': f'Plantilla desconocida: {template_id}'}), 404
    return Response(rendered['html'], mimetype='text/html')


@emails_bp.route('/api/emails/<template_id>/send', methods=['POST'])
@login_required
def send_email(template_id):
    data = request.get_json(silent=True) or {}
    to = data.get('to')
    if not to:
        return jsonify({'error': "Campo requerido: 'to'"}), 400
    try:
        result = EmailService.send(template_id, to, data.get('context'))
    except KeyError:
        return jsonify({'error': f'Plantilla desconocida: {template_id}'}), 404
    return jsonify(result)

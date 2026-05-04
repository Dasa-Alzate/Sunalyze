"""Endpoints RGPD: export portable (Art. 15/20) y supresion (Art. 17).

Capa HTTP fina sobre GdprService. El usuario actua siempre sobre SUS propios
datos (current_user); los endpoints estan gateados por permiso.
"""

from flask import Blueprint, jsonify, Response

from app.services.gdpr_service import GdprService
from app.security import current_user, logout_user, login_required
from app.authz import require_permission, Permission

gdpr_bp = Blueprint('gdpr', __name__)


@gdpr_bp.route('/api/gdpr/consent', methods=['POST'])
@login_required
def accept_privacy():
    user = GdprService.accept_privacy(current_user())
    return jsonify({'ok': True, 'privacy_accepted_at': user.privacy_accepted_at.isoformat()})


@gdpr_bp.route('/api/gdpr/export', methods=['GET'])
@require_permission(Permission.ACCOUNT_EXPORT)
def export_data():
    return jsonify(GdprService.export_data(current_user()))


@gdpr_bp.route('/api/gdpr/export.zip', methods=['GET'])
@require_permission(Permission.ACCOUNT_EXPORT)
def export_zip():
    user = current_user()
    payload = GdprService.export_zip(user)
    filename = f'sunalyze-export-user-{user.id}.zip'
    return Response(
        payload,
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


@gdpr_bp.route('/api/gdpr/account', methods=['DELETE'])
@require_permission(Permission.ACCOUNT_DELETE)
def erase_account():
    GdprService.erase_account(current_user())
    logout_user()
    return jsonify({'ok': True, 'message': 'Tu cuenta ha sido eliminada y tus datos anonimizados.'})

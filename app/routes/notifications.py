
from flask import Blueprint, request, jsonify

from app.security import current_user, current_org_id, login_required
from app.services.notification_service import NotificationService
from app.services.pending_work_service import PendingWorkService

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/api/notifications', methods=['GET'])
@login_required
def list_notifications():
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get('per_page', 20))
    except (TypeError, ValueError):
        per_page = 20
    return jsonify(NotificationService.list_for(
        current_user().id, current_org_id(), page=page, per_page=per_page,
    ))


@notifications_bp.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def unread_count():
    count = NotificationService.unread_count(current_user().id, current_org_id())
    return jsonify({'unread_count': count})


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = NotificationService.mark_read(
        current_user().id, current_org_id(), notification_id,
    )
    return jsonify(notification.to_dict())


@notifications_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    updated = NotificationService.mark_all_read(current_user().id, current_org_id())
    return jsonify({'ok': True, 'updated': updated})


@notifications_bp.route('/api/pending-work', methods=['GET'])
@login_required
def pending_work():
    return jsonify(PendingWorkService.derive(current_user(), current_org_id()))

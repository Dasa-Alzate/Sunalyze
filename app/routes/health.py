
import uuid

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import cache, db, limiter

health_bp = Blueprint('health', __name__)


def _check_db():
    try:
        db.session.execute(text('SELECT 1'))
        return 'ok'
    except Exception:
        return 'error'


def _check_cache():
    try:
        key = f'health:{uuid.uuid4().hex}'
        cache.set(key, '1', timeout=5)
        value = cache.get(key)
        cache.delete(key)
        return 'ok' if value == '1' else 'error'
    except Exception:
        return 'error'


@health_bp.route('/health')
@limiter.exempt
def health():
    db_status = _check_db()
    cache_status = _check_cache()
    if db_status == 'ok':
        return jsonify({'status': 'ok', 'db': db_status, 'cache': cache_status}), 200
    return jsonify({'status': 'degraded', 'db': db_status, 'cache': cache_status}), 503

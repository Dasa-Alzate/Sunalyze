"""Protecciones del portal de superadmin: IP allowlist, gate de rol y auditoría.

Capas (de fuera hacia dentro):
1. `enforce_ip`  — before_request del blueprint: filtra por IP ANTES del login.
2. `require_superadmin` — exige sesión + User.is_superadmin en cada vista.
3. `log_action` — deja rastro auditado (actor, IP, acción) de todo efecto.
"""

import ipaddress
from functools import wraps

from flask import current_app, request, redirect, url_for, abort, render_template

from app.extensions import db
from app.security import current_user
from app.models.superadmin_audit import SuperadminAudit


def client_ip():
    if current_app.config.get('SUPERADMIN_TRUST_PROXY'):
        forwarded = request.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _allowlist():
    raw = current_app.config.get('SUPERADMIN_IP_ALLOWLIST') or ''
    networks = []
    for token in raw.replace(';', ',').split(','):
        token = token.strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            current_app.logger.warning('SUPERADMIN_IP_ALLOWLIST: entrada inválida «%s»', token)
    return networks


def ip_allowed():
    networks = _allowlist()
    if not networks:
        return True
    try:
        addr = ipaddress.ip_address(client_ip())
    except ValueError:
        return False
    return any(addr in net for net in networks)


def enforce_ip():
    if not ip_allowed():
        return render_template('superadmin/denied.html', ip=client_ip()), 403


def is_superadmin():
    user = current_user()
    return bool(user and user.is_superadmin)


def require_superadmin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for('superadmin.login', next=request.path))
        if not is_superadmin():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def log_action(action, target=None, detail=None):
    user = current_user()
    entry = SuperadminAudit(
        actor_user_id=user.id if user else None,
        actor_email=user.email if user else None,
        ip=client_ip(),
        action=action,
        target=target,
        detail=detail,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


from functools import wraps

from flask import request, redirect, url_for, abort, render_template, session

from app.extensions import db
from app.ip_allowlist import client_ip, ip_allowed
from app.security import current_user
from app.models.user import User
from app.models.superadmin_audit import SuperadminAudit

_PENDING_MFA_KEY = 'pending_mfa_user_id'


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


def set_pending_mfa(user):
    session[_PENDING_MFA_KEY] = user.id


def clear_pending_mfa():
    session.pop(_PENDING_MFA_KEY, None)


def pending_mfa_user():
    user_id = session.get(_PENDING_MFA_KEY)
    if not user_id:
        return None
    return User.query.get(user_id)


def log_action(action, target=None, detail=None, actor=None):
    user = actor or current_user()
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

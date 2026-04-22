"""Sesion de usuario: helpers y decorador de autorizacion.

Auth por cookie de sesion firmada (misma-origen SPA + Flask). Guarda el
usuario activo y el workspace activo (org_id) en la sesion.
"""

from functools import wraps
from flask import session, g

from app.models.user import User
from app.errors import Unauthorized, Forbidden


def login_user(user, org_id=None, remember=True):
    session['user_id'] = user.id
    session['org_id'] = org_id or (user.personal_org.id if user.personal_org else None)
    session.permanent = remember
    g.pop('_current_user', None)


def logout_user():
    session.clear()
    g.pop('_current_user', None)


def current_user():
    if 'user_id' not in session:
        return None
    if '_current_user' not in g:
        g._current_user = User.query.get(session['user_id'])
    return g._current_user


def current_org_id():
    return session.get('org_id')


def set_current_org(org_id):
    session['org_id'] = org_id


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            raise Unauthorized('Inicia sesión para continuar.')
        return fn(*args, **kwargs)
    return wrapper


def require_membership(org_id):
    user = current_user()
    if user is None:
        raise Unauthorized('Inicia sesión para continuar.')
    if not any(m.org_id == org_id for m in user.memberships):
        raise Forbidden('No tienes acceso a este workspace.')

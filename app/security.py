
from functools import wraps
from flask import session, g

from app.models.user import User
from app.errors import Unauthorized


def login_user(user, org_id=None, remember=True):
    session['user_id'] = user.id
    session['org_id'] = org_id or (user.personal_org.id if user.personal_org else None)
    session['session_gen'] = user.session_gen or 0
    session.permanent = remember
    g.pop('_current_user', None)


def logout_user():
    session.clear()
    g.pop('_current_user', None)


def current_user():
    if 'user_id' not in session:
        return None
    if '_current_user' not in g:
        user = User.query.get(session['user_id'])
        valid = (
            user is not None
            and not user.is_deleted
            and session.get('session_gen', 0) == (user.session_gen or 0)
        )
        g._current_user = user if valid else None
    return g._current_user


def current_org_id():
    return session.get('org_id')


def set_current_org(org_id):
    session['org_id'] = org_id


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            raise Unauthorized('Inicia sesión para continuar.', code='auth.login_required')
        return fn(*args, **kwargs)
    return wrapper

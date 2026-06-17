"""Autorizacion RBAC: permisos, matriz rol->permisos y decorador de endpoint.

Separado de la autenticacion (security.py). Los permisos se evaluan contra el
rol del usuario en el WORKSPACE ACTIVO (Membership.role), no contra el usuario
global: la misma persona puede ser 'owner' de su espacio y 'member' de una
empresa. La matriz vive en un unico sitio (ROLE_PERMISSIONS) para mantenerla.
"""

from functools import wraps
from flask import g

from app.security import current_user, current_org_id
from app.models.membership import Membership
from app.errors import Unauthorized, Forbidden


class Permission:
    PROJECT_VIEW = 'project:view'
    PROJECT_CREATE = 'project:create'
    PROJECT_EDIT = 'project:edit'
    PROJECT_DELETE = 'project:delete'
    PROJECT_LEGALIZE = 'project:legalize'
    MEMORIA_SIGN = 'memoria:sign'
    EQUIPMENT_VIEW = 'equipment:view'
    EQUIPMENT_EDIT = 'equipment:edit'
    CATALOG_SUBSCRIBE = 'catalog:subscribe'
    CATALOG_MANAGE = 'catalog:manage'
    MEMBER_INVITE = 'member:invite'
    MEMBER_MANAGE = 'member:manage'
    ORG_MANAGE = 'org:manage'


ALL_PERMISSIONS = frozenset(
    v for k, v in vars(Permission).items() if not k.startswith('_') and isinstance(v, str)
)

_MEMBER = {
    Permission.PROJECT_VIEW, Permission.PROJECT_CREATE, Permission.PROJECT_EDIT,
    Permission.MEMORIA_SIGN,
    Permission.EQUIPMENT_VIEW, Permission.EQUIPMENT_EDIT,
    Permission.CATALOG_SUBSCRIBE,
}

_ADMIN = _MEMBER | {
    Permission.PROJECT_DELETE,
    Permission.PROJECT_LEGALIZE,
    Permission.CATALOG_MANAGE,
    Permission.MEMBER_INVITE, Permission.MEMBER_MANAGE,
}

ROLE_PERMISSIONS = {
    'owner': set(ALL_PERMISSIONS),
    'admin': _ADMIN,
    'member': _MEMBER,
}


def current_role():
    user = current_user()
    org_id = current_org_id()
    if not user or not org_id:
        return None
    if '_role' not in g:
        membership = Membership.query.filter_by(user_id=user.id, org_id=org_id).first()
        g._role = membership.role if membership else None
    return g._role


def current_permissions():
    return ROLE_PERMISSIONS.get(current_role(), set())


def has_permission(permission):
    return permission in current_permissions()


def require_permission(*permissions):
    """Exige sesion + que el rol en el workspace activo conceda los permisos.

    Uso: @require_permission(Permission.PROJECT_EDIT)
    401 si no hay sesion; 403 si el rol no concede algun permiso requerido.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user() is None:
                raise Unauthorized('Inicia sesión para continuar.')
            if current_role() is None:
                raise Forbidden('No tienes acceso a este workspace.')
            granted = current_permissions()
            if not all(p in granted for p in permissions):
                raise Forbidden('No tienes permiso para realizar esta acción.')
            return fn(*args, **kwargs)
        return wrapper
    return decorator

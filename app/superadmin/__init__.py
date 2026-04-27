"""Portal de superadmin: blueprint Jinja con guardas, servible en subdominio.

`register_superadmin(app)` lo monta en el subdominio configurado
(`SUPERADMIN_SUBDOMAIN` + `SERVER_NAME`) o, en su defecto, bajo `/superadmin`
para desarrollo local. El filtro de IP corre como before_request del blueprint.
"""

from app.superadmin.views import superadmin_bp
from app.superadmin.guards import enforce_ip

superadmin_bp.before_request(enforce_ip)


def register_superadmin(app):
    subdomain = app.config.get('SUPERADMIN_SUBDOMAIN')
    server_name = app.config.get('SERVER_NAME')
    if subdomain and server_name:
        app.register_blueprint(superadmin_bp, subdomain=subdomain)
    else:
        app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

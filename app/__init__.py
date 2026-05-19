"""
Sunalyze - Aplicacion web para el analisis y dimensionamiento de instalaciones fotovoltaicas.

Calcula requisitos de paneles solares, compatibilidad de inversores y genera
documentacion tecnica utilizando datos de irradiancia de PVGIS.
"""

import logging
import os
from flask import Flask, send_from_directory

from app.extensions import db, cache, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db, render_as_batch=app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info('Sunalyze application started')

    from app.models import (  # noqa: F401
        panel, inverter, wire, installation_defaults, project,
        user, organization, membership, catalog, invitation,
        support_ticket, superadmin_audit, scrape_run, audit_event,
        memoria_signature, project_event,
    )

    from app.routes.main import bp as main_bp
    from app.routes.crud import crud_bp
    from app.routes.circuit import circuit_bp
    from app.routes.projects import projects_bp
    from app.routes.emails import emails_bp
    from app.routes.auth import auth_bp
    from app.routes.catalogs import catalogs_bp
    from app.routes.members import members_bp
    from app.routes.audit import audit_bp
    from app.routes.gdpr import gdpr_bp
    from app.routes.legalization import legalization_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(crud_bp)
    app.register_blueprint(circuit_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalogs_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(gdpr_bp)
    app.register_blueprint(legalization_bp)

    from app.errors import register_error_handlers
    register_error_handlers(app)

    from app.cli import register_cli
    register_cli(app)

    from app.security_headers import register_security
    register_security(app)

    from app.superadmin import register_superadmin
    register_superadmin(app)

    _register_spa(app)

    return app


def _register_spa(app):
    """Sirve la SPA de React compilada (frontend/dist).

    Las rutas explicitas de la API y /static tienen prioridad en el mapa de
    URLs de Werkzeug; este catch-all solo atiende lo que no coincida, de modo
    que el enrutado del lado cliente (React Router) recae siempre en index.html.
    """
    dist_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'frontend', 'dist',
    )

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        candidate = os.path.join(dist_dir, path)
        if path and os.path.isfile(candidate):
            return send_from_directory(dist_dir, path)
        index = os.path.join(dist_dir, 'index.html')
        if os.path.isfile(index):
            return send_from_directory(dist_dir, 'index.html')
        return (
            "<h1>Sunalyze</h1><p>El frontend de React no esta compilado. "
            "Ejecuta:</p><pre>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</pre>"
            "<p>En desarrollo usa el servidor de Vite: <code>cd frontend &amp;&amp; npm run dev</code></p>",
            200,
        )

"""
Sunalyze - Aplicacion web para el analisis y dimensionamiento de instalaciones fotovoltaicas.

Calcula requisitos de paneles solares, compatibilidad de inversores y genera
documentacion tecnica utilizando datos de irradiancia de PVGIS.
"""

import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

db = SQLAlchemy()
cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    cache.init_app(app)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info('Sunalyze application started')

    # Registrar blueprints
    from app.routes.main import bp as main_bp
    from app.routes.crud import crud_bp
    from app.routes.circuit import circuit_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(crud_bp)
    app.register_blueprint(circuit_bp)

    return app
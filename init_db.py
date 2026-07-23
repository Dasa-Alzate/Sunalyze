import logging

from app import create_app, db
from app.utils.data_loader import load_initial_data

logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    db.create_all()
    logger.info("Tablas creadas exitosamente!")

    load_initial_data()

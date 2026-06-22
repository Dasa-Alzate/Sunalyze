"""Utilidades de persistencia para cerrar condiciones de carrera TOCTOU.

El patron `if existe: error; else crear` tiene una ventana de carrera entre la
comprobacion y la insercion. El arbitro atomico correcto es la constraint UNIQUE
de la base de datos: aqui hacemos commit y traducimos el IntegrityError a un
error de dominio en lugar de dejarlo escalar a un 500.
"""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.errors import Conflict


def commit_or_conflict(message):
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(message, code='error.conflict')

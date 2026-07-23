
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.errors import Conflict


def commit_or_conflict(message):
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(message, code='error.conflict')

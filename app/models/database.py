"""Modelo base abstracto con campos comunes para todas las entidades."""

from app import db
from datetime import datetime

class BaseModel(db.Model):
    """Modelo base abstracto que proporciona id, created_at y updated_at a todas las entidades."""
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
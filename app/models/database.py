"""Modelo base abstracto con campos comunes para todas las entidades.

Política de borrado (ver `docs/deletion-policy-research.md`):

- Las raíces de tenant/catálogo (`Organization`, `User`, `Project`, `Catalog`) usan
  soft-delete (`SoftDeleteMixin`): el borrado normal marca `deleted_at` y nunca hard-deletea.
  El derecho al olvido (`GdprService.erase_account`) anonimiza la PII en sitio y soft-deletea.
- El resto de FKs llevan `ondelete` coherente para que un hard-delete sea seguro:
  - `CASCADE` en hijos de propiedad (composición), alineado con `cascade='all, delete-orphan'`
    y `passive_deletes=True` en el ORM.
  - `SET NULL` en referencias a actor/autor (el registro sobrevive sin actor); su columna es
    `nullable=True`.
  - `RESTRICT` (default, sin `ondelete`) en referencias de lookup/catálogo, donde borrar el
    padre referenciado no debe permitirse silenciosamente.
"""

from app import db
from datetime import datetime

class BaseModel(db.Model):
    """Modelo base abstracto que proporciona id, created_at y updated_at a todas las entidades."""
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """Borrado lógico via `deleted_at`.

    En lugar de eliminar la fila se marca el instante de borrado, preservando la
    integridad referencial y la retención legal de documentos asociados. La
    propiedad `is_deleted` y los helpers de consulta `active`/`with_deleted`
    centralizan el filtrado por defecto (no devolver borrados).
    """
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        if self.deleted_at is None:
            self.deleted_at = datetime.utcnow()

    @classmethod
    def active(cls):
        """Query base que excluye los registros borrados logicamente."""
        return cls.query.filter(cls.deleted_at.is_(None))

    @classmethod
    def with_deleted(cls):
        """Escape hatch: query que incluye tambien los registros borrados."""
        return cls.query
"""Mixin de procedencia para equipos: de dónde salió el dato y si está bloqueado.

`is_locked` protege ediciones humanas: un scraper no debe pisar un equipo que
alguien corrigió a mano. `source='manual'` es el valor por defecto (alta humana).
"""

from app.extensions import db


class ProvenanceMixin:
    source = db.Column(db.String(50), nullable=False, default='manual')
    source_url = db.Column(db.String(500))
    external_id = db.Column(db.String(120), index=True)
    scraped_at = db.Column(db.DateTime)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)

    def provenance_dict(self):
        return {
            'source': self.source,
            'source_url': self.source_url,
            'external_id': self.external_id,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'is_locked': self.is_locked,
        }


from datetime import datetime

from app.extensions import db


class ProvenanceMixin:
    source = db.Column(db.String(50), nullable=False, default='manual')
    source_url = db.Column(db.String(500))
    external_id = db.Column(db.String(120), index=True)
    scraped_at = db.Column(db.DateTime)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    needs_review = db.Column(db.Boolean, nullable=False, default=False)
    review_notes = db.Column(db.String(500))
    verified_by = db.Column(db.String(255))
    verified_at = db.Column(db.DateTime)

    @property
    def is_scraped(self):
        return bool(self.source and self.source.startswith('scraper:') and not self.is_locked)

    @property
    def is_verified(self):
        return self.verified_at is not None

    def mark_verified(self, actor):
        self.verified_by = (getattr(actor, 'email', None) or str(actor))[:255] if actor else None
        self.verified_at = datetime.utcnow()

    def provenance_dict(self):
        return {
            'source': self.source,
            'source_url': self.source_url,
            'external_id': self.external_id,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'is_locked': self.is_locked,
            'needs_review': self.needs_review,
            'review_notes': self.review_notes,
            'scraped': self.is_scraped,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified': self.is_verified,
        }


from app.extensions import db
from .database import BaseModel


class ScrapeRun(BaseModel):
    __tablename__ = 'scrape_runs'

    brand = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='running')
    dry_run = db.Column(db.Boolean, nullable=False, default=False)
    created_count = db.Column(db.Integer, nullable=False, default=0)
    updated_count = db.Column(db.Integer, nullable=False, default=0)
    skipped_count = db.Column(db.Integer, nullable=False, default=0)
    error_count = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'status': self.status,
            'dry_run': self.dry_run,
            'created': self.created_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count,
            'errors': self.error_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'notes': self.notes,
        }

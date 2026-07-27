
from app.extensions import db
from .database import BaseModel


class ScrapeCache(BaseModel):
    __tablename__ = 'scrape_cache'

    url_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    url = db.Column(db.String(500), nullable=False)
    etag = db.Column(db.String(200))
    last_modified = db.Column(db.String(120))
    content_hash = db.Column(db.String(64))
    fetched_at = db.Column(db.DateTime)
    hit_count = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'etag': self.etag,
            'last_modified': self.last_modified,
            'content_hash': self.content_hash,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'hit_count': self.hit_count,
        }

    def __repr__(self):
        return f'<ScrapeCache {self.url[:60]}>'

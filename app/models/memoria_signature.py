
from app.extensions import db
from .database import BaseModel


class MemoriaSignature(BaseModel):
    __tablename__ = 'memoria_signatures'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    signed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    pdf_sha256 = db.Column(db.String(64), nullable=False)
    pdf_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    is_current = db.Column(db.Boolean, nullable=False, default=True, index=True)

    signed_by = db.relationship('User', foreign_keys=[signed_by_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'signed_by_user_id': self.signed_by_user_id,
            'signed_by': self.signed_by.full_name if self.signed_by else None,
            'pdf_sha256': self.pdf_sha256,
            'pdf_size_bytes': self.pdf_size_bytes,
            'is_current': self.is_current,
            'signed_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<MemoriaSignature p{self.project_id} {self.pdf_sha256[:8]}>'

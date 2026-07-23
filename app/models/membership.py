
from app.extensions import db
from .database import BaseModel

ROLES = ('owner', 'admin', 'member')


class Membership(BaseModel):
    __tablename__ = 'memberships'
    __table_args__ = (db.UniqueConstraint('user_id', 'org_id', name='uq_member_user_org'),)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='member')

    user = db.relationship('User', back_populates='memberships')
    organization = db.relationship('Organization', back_populates='memberships')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'org_id': self.org_id,
            'role': self.role,
        }

    def __repr__(self):
        return f'<Membership u{self.user_id}/o{self.org_id} {self.role}>'

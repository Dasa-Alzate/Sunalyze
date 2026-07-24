
import json

from app.extensions import db
from .database import BaseModel, SoftDeleteMixin

ORG_TYPES = ('PERSONAL', 'BUSINESS')
PLANS = ('free', 'pro', 'business')


class Organization(BaseModel, SoftDeleteMixin):
    __tablename__ = 'organizations'

    nombre = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='PERSONAL')
    plan = db.Column(db.String(20), nullable=False, default='free')
    seats = db.Column(db.Integer, nullable=False, default=1)

    memberships = db.relationship(
        'Membership', back_populates='organization',
        cascade='all, delete-orphan', passive_deletes=True,
    )

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'type': self.type,
            'plan': self.plan,
            'seats': self.seats,
            'member_count': len(self.memberships),
        }

    def __repr__(self):
        return f'<Organization {self.nombre} ({self.type}/{self.plan})>'


class OrgBrandingProfile(BaseModel):

    __tablename__ = 'org_branding_profiles'
    __table_args__ = (
        db.UniqueConstraint('org_id', name='uq_org_branding_org'),
    )

    org_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    logo_path = db.Column(db.String(500))
    primary_color = db.Column(db.String(20))
    footer_text = db.Column(db.String(300))
    project_prefix = db.Column(db.String(8))

    organization = db.relationship('Organization')

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'logo_path': self.logo_path,
            'primary_color': self.primary_color,
            'footer_text': self.footer_text,
            'project_prefix': self.project_prefix,
        }

    def __repr__(self):
        return f'<OrgBrandingProfile org{self.org_id}>'


class OrgBudgetProfile(BaseModel):

    __tablename__ = 'org_budget_profiles'
    __table_args__ = (
        db.UniqueConstraint('org_id', name='uq_org_budget_org'),
    )

    org_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    labor_fixed = db.Column(db.Float, nullable=False, default=0)
    labor_per_panel = db.Column(db.Float, nullable=False, default=0)
    equipment_inflation_pct = db.Column(db.Float, nullable=False, default=0)
    _custom_lines = db.Column('custom_lines', db.Text)

    organization = db.relationship('Organization')

    @property
    def custom_lines(self):
        if not self._custom_lines:
            return []
        try:
            return json.loads(self._custom_lines)
        except (ValueError, TypeError):
            return []

    @custom_lines.setter
    def custom_lines(self, value):
        self._custom_lines = json.dumps(value) if value else None

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'labor_fixed': self.labor_fixed,
            'labor_per_panel': self.labor_per_panel,
            'equipment_inflation_pct': self.equipment_inflation_pct,
            'custom_lines': self.custom_lines,
        }

    def __repr__(self):
        return f'<OrgBudgetProfile org{self.org_id}>'

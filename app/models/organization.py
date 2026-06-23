"""Workspace/tenant. Una persona o autonomo es un workspace de un solo miembro."""

from app.extensions import db
from .database import BaseModel, SoftDeleteMixin

ORG_TYPES = ('PERSONAL', 'BUSINESS')
PLANS = ('free', 'pro', 'business')


class Organization(BaseModel, SoftDeleteMixin):
    """Unico eje de propiedad de los datos.

    La diferencia entre persona/autonomo y empresa es configuracion (type +
    plan + nº de miembros), no un modelo de datos distinto.
    """
    __tablename__ = 'organizations'

    nombre = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='PERSONAL')
    plan = db.Column(db.String(20), nullable=False, default='free')
    seats = db.Column(db.Integer, nullable=False, default=1)

    memberships = db.relationship('Membership', back_populates='organization', cascade='all, delete-orphan')

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
    """Marca de la organización aplicada al render de documentos (1:1 con la org).

    Org-scoped. Sin fila de branding, los documentos se renderizan con el estilo por defecto.
    `logo_path` es relativa a `instance_path`; `primary_color` es un color CSS; `footer_text` es
    el pie de página del PDF.
    """

    __tablename__ = 'org_branding_profiles'
    __table_args__ = (
        db.UniqueConstraint('org_id', name='uq_org_branding_org'),
    )

    org_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True
    )
    logo_path = db.Column(db.String(500))
    primary_color = db.Column(db.String(20))
    footer_text = db.Column(db.String(300))

    organization = db.relationship('Organization')

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'logo_path': self.logo_path,
            'primary_color': self.primary_color,
            'footer_text': self.footer_text,
        }

    def __repr__(self):
        return f'<OrgBrandingProfile org{self.org_id}>'

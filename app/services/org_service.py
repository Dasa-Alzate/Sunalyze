"""Servicios de organización: perfil de marca (branding) aplicado al render de documentos.

Org-scoped: el branding es 1:1 con la organización del workspace activo, así que la
propiedad se deriva de `org_id` (sin IDOR por recurso). El perfil se crea perezosamente la
primera vez que se guarda.
"""

from app.extensions import db
from app.models.organization import OrgBrandingProfile


class OrgService:

    @staticmethod
    def get_branding(org_id):
        profile = OrgBrandingProfile.query.filter_by(org_id=org_id).first()
        if profile is not None:
            return profile.to_dict()
        return {
            'id': None,
            'org_id': org_id,
            'logo_path': None,
            'primary_color': None,
            'footer_text': None,
        }

    @staticmethod
    def update_branding(org_id, fields):
        profile = OrgBrandingProfile.query.filter_by(org_id=org_id).first()
        if profile is None:
            profile = OrgBrandingProfile(org_id=org_id)
            db.session.add(profile)
        for attr in ('logo_path', 'primary_color', 'footer_text'):
            if attr in fields:
                value = fields[attr]
                setattr(profile, attr, value.strip() if isinstance(value, str) else value)
        db.session.commit()
        return profile.to_dict()

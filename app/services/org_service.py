"""Servicios de organización: perfil de marca (branding) aplicado al render de documentos.

Org-scoped: el branding es 1:1 con la organización del workspace activo, así que la
propiedad se deriva de `org_id` (sin IDOR por recurso). El perfil se crea perezosamente la
primera vez que se guarda.

El logo se almacena en el árbol de la instancia bajo `cfiles/<org_id>/logo.<ext>` (un único
fichero por organización, se reemplaza en cada subida). `logo_path` queda relativa a
`instance_path`, que es lo que embebe el `pdf_url_fetcher` al renderizar documentos.
"""

import glob
import io
import os

from app.errors import ValidationError
from app.extensions import db
from app.models.organization import OrgBrandingProfile

_BRANDING_ATTRS = ('logo_path', 'primary_color', 'footer_text', 'project_prefix')
_LOGO_DIRNAME = 'cfiles'
_MAX_LOGO_BYTES = 2 * 1024 * 1024
_RASTER_EXT = {'png': 'png', 'jpeg': 'jpg', 'webp': 'webp'}


def _sniff_image_ext(data):
    """Devuelve la extensión canónica si `data` es una imagen soportada, si no None.

    Valida el tipo real del contenido (no la extensión declarada): png/jpeg/webp vía Pillow,
    svg por olfateo del prólogo XML/`<svg`.
    """
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
            fmt = (im.format or '').lower()
        if fmt in _RASTER_EXT:
            return _RASTER_EXT[fmt]
    except (UnidentifiedImageError, OSError, ValueError):
        pass

    head = data[:512].lstrip(b'\xef\xbb\xbf \t\r\n')
    lowered = head.lower()
    if lowered.startswith(b'<?xml') or lowered.startswith(b'<svg'):
        if b'<svg' in data[:4096].lower():
            return 'svg'
    return None


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
            'project_prefix': None,
        }

    @staticmethod
    def _get_or_create(org_id):
        profile = OrgBrandingProfile.query.filter_by(org_id=org_id).first()
        if profile is None:
            profile = OrgBrandingProfile(org_id=org_id)
            db.session.add(profile)
        return profile

    @staticmethod
    def update_branding(org_id, fields):
        profile = OrgService._get_or_create(org_id)
        for attr in _BRANDING_ATTRS:
            if attr in fields:
                value = fields[attr]
                setattr(profile, attr, value.strip() if isinstance(value, str) else value)
        db.session.commit()
        return profile.to_dict()

    @staticmethod
    def save_logo(org_id, instance_path, data):
        """Valida, reemplaza y persiste el logo de la organización.

        Rechaza (422) lo que no sea imagen png/jpeg/webp/svg o supere el tamaño máximo. Borra
        cualquier `logo.*` previo para no acumular y actualiza `logo_path` (relativa a
        `instance_path`).
        """
        if not data:
            raise ValidationError('El logo está vacío.')
        if len(data) > _MAX_LOGO_BYTES:
            raise ValidationError('El logo supera el tamaño máximo permitido (2 MB).')
        ext = _sniff_image_ext(data)
        if ext is None:
            raise ValidationError('El logo debe ser una imagen PNG, JPEG, WebP o SVG.')

        rel_dir = f'{_LOGO_DIRNAME}/{org_id}'
        abs_dir = os.path.join(instance_path, _LOGO_DIRNAME, str(org_id))
        os.makedirs(abs_dir, exist_ok=True)
        for previous in glob.glob(os.path.join(abs_dir, 'logo.*')):
            os.remove(previous)
        filename = f'logo.{ext}'
        with open(os.path.join(abs_dir, filename), 'wb') as fh:
            fh.write(data)

        profile = OrgService._get_or_create(org_id)
        profile.logo_path = f'{rel_dir}/{filename}'
        db.session.commit()
        return profile.to_dict()

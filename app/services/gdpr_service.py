"""Logica de dominio RGPD: portabilidad de datos y derecho al olvido.

Aisla las reglas de los Art. 15/20 (export portable) y Art. 17 (supresion via
anonimizacion + soft-delete) del transporte HTTP. No toca request/response;
devuelve estructuras serializables o lanza DomainError.
"""

import io
import json
import logging
import zipfile
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.errors import NotFound, Conflict

logger = logging.getLogger(__name__)

EXPORT_FORMAT_VERSION = '1.0'


class GdprService:

    @staticmethod
    def _owned_org_ids(user):
        """Ids de organizaciones (no borradas) donde el usuario es owner."""
        return [m.org_id for m in user.memberships if m.role == 'owner']

    @staticmethod
    def accept_privacy(user):
        """Registra el consentimiento de privacidad con su instante (flag minimo)."""
        user.privacy_accepted_at = datetime.utcnow()
        db.session.commit()
        return user

    @staticmethod
    def export_data(user):
        """Construye el volcado portable de los datos personales del usuario.

        Cubre perfil y membresias (Art. 15) y los datos de las organizaciones que
        posee como owner, incluidos sus proyectos (Art. 20). En formato JSON, de
        uso comun y lectura mecanica. No incluye secretos (password_hash).
        """
        profile = user.to_dict()
        profile.pop('organizations', None)

        memberships = []
        for m in user.memberships:
            org = m.organization
            memberships.append({
                'org_id': m.org_id,
                'role': m.role,
                'org_nombre': org.nombre if org else None,
            })

        owned = []
        owned_ids = GdprService._owned_org_ids(user)
        for org_id in owned_ids:
            org = Organization.with_deleted().filter_by(id=org_id).first()
            if not org:
                continue
            projects = Project.query.filter_by(org_id=org_id).all()
            owned.append({
                'organization': org.to_dict(),
                'projects': [p.to_dict() for p in projects],
            })

        return {
            'export_metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'gdpr_articles': ['15', '20'],
                'format_version': EXPORT_FORMAT_VERSION,
            },
            'user': profile,
            'memberships': memberships,
            'owned_organizations': owned,
        }

    @staticmethod
    def export_zip(user):
        """Empaqueta el export JSON en un ZIP en memoria (stdlib zipfile)."""
        payload = GdprService.export_data(user)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                f'sunalyze-export-user-{user.id}.json',
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def erase_account(user):
        """Ejercita el derecho al olvido (Art. 17) sobre la cuenta del usuario.

        Anonimiza la PII directa del usuario y lo soft-deletea. Las organizaciones
        personales de las que es unico miembro se soft-deletean tambien, pero sus
        proyectos se conservan por retencion legal de la documentacion tecnica. En
        una organizacion compartida no se permite la supresion si el usuario es el
        unico owner: debe transferir la propiedad antes (preserva el acceso del
        equipo y la integridad del workspace).
        """
        if user.is_deleted:
            raise Conflict('La cuenta ya fue eliminada.', code='account.already_deleted')

        for org_id in GdprService._owned_org_ids(user):
            org = Organization.active().filter_by(id=org_id).first()
            if not org:
                continue
            member_ids = [m.user_id for m in org.memberships]
            other_owners = [
                m for m in org.memberships
                if m.role == 'owner' and m.user_id != user.id
            ]
            if member_ids == [user.id]:
                org.soft_delete()
            elif not other_owners:
                raise Conflict(
                    f'Transfiere la propiedad del workspace "{org.nombre}" antes de '
                    'eliminar tu cuenta.'
                )

        for m in list(user.memberships):
            db.session.delete(m)

        user.anonymize()
        user.soft_delete()
        db.session.commit()
        logger.info('Cuenta anonimizada y soft-deleteada: user %s', user.id)
        return user

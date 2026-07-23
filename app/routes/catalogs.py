
from flask import Blueprint, request, jsonify

from app.extensions import db
from app.schemas.catalog import CatalogSchema
from app.services.catalog_service import CatalogService
from app.services.audit_service import AuditService
from app.security import current_org_id, current_user
from app.authz import require_permission, Permission

catalogs_bp = Blueprint('catalogs', __name__)


@catalogs_bp.route('/api/catalogs', methods=['GET'])
@require_permission(Permission.EQUIPMENT_VIEW)
def list_catalogs():
    if request.args.get('deleted', '').lower() in ('1', 'true', 'yes'):
        return list_deleted_catalogs()
    return jsonify(CatalogService.library(current_org_id()))


@require_permission(Permission.CATALOG_MANAGE)
def list_deleted_catalogs():
    return jsonify(CatalogService.deleted_library(current_org_id()))


@catalogs_bp.route('/api/catalogs', methods=['POST'])
@require_permission(Permission.CATALOG_MANAGE)
def create_catalog():
    data = CatalogSchema(**(request.get_json(silent=True) or {}))
    catalog = CatalogService.create_catalog(current_org_id(), data.nombre, data.descripcion)
    AuditService.record(
        'catalog.create', actor=current_user(), org_id=current_org_id(),
        entity_type='catalog', entity_id=catalog.id,
        payload={'nombre': catalog.nombre},
    )
    db.session.commit()
    return jsonify({**catalog.to_dict(), 'own': True, 'subscribed': False,
                    'counts': {'panels': 0, 'inverters': 0, 'batteries': 0, 'wires': 0}}), 201


@catalogs_bp.route('/api/catalogs/<int:catalog_id>', methods=['DELETE'])
@require_permission(Permission.CATALOG_MANAGE)
def delete_catalog(catalog_id):
    catalog = CatalogService.delete_catalog(current_org_id(), catalog_id)
    AuditService.record(
        'catalog.delete', actor=current_user(), org_id=current_org_id(),
        entity_type='catalog', entity_id=catalog.id,
        payload={'nombre': catalog.nombre},
    )
    db.session.commit()
    return jsonify({'message': 'Catálogo eliminado'})


@catalogs_bp.route('/api/catalogs/<int:catalog_id>', methods=['PATCH'])
@require_permission(Permission.CATALOG_MANAGE)
def update_catalog(catalog_id):
    data = request.get_json(silent=True) or {}
    org_id = current_org_id()
    user = current_user()
    catalog = CatalogService.set_color(
        org_id, catalog_id, data.get('color'),
        allow_marketplace=bool(getattr(user, 'is_superadmin', False)),
    )
    AuditService.record(
        'catalog.update', actor=user, org_id=org_id,
        entity_type='catalog', entity_id=catalog.id,
        payload={'nombre': catalog.nombre, 'color': catalog.color},
    )
    db.session.commit()
    return jsonify({**catalog.to_dict(), 'own': catalog.org_id == org_id})


@catalogs_bp.route('/api/catalogs/<int:catalog_id>/restore', methods=['POST'])
@require_permission(Permission.CATALOG_MANAGE)
def restore_catalog(catalog_id):
    catalog = CatalogService.restore_catalog(current_org_id(), catalog_id)
    AuditService.record(
        'catalog.restore', actor=current_user(), org_id=current_org_id(),
        entity_type='catalog', entity_id=catalog.id,
        payload={'nombre': catalog.nombre},
    )
    db.session.commit()
    return jsonify({**catalog.to_dict(), 'own': True})


@catalogs_bp.route('/api/marketplace', methods=['GET'])
@require_permission(Permission.EQUIPMENT_VIEW)
def marketplace():
    return jsonify(CatalogService.marketplace(current_org_id()))


@catalogs_bp.route('/api/catalogs/<int:catalog_id>/subscribe', methods=['POST'])
@require_permission(Permission.CATALOG_SUBSCRIBE)
def subscribe(catalog_id):
    catalog = CatalogService.subscribe(current_org_id(), catalog_id)
    AuditService.record(
        'catalog.subscribe', actor=current_user(), org_id=current_org_id(),
        entity_type='catalog', entity_id=catalog.id,
        payload={'nombre': catalog.nombre},
    )
    db.session.commit()
    return jsonify({'ok': True, 'catalog': catalog.to_dict()})


@catalogs_bp.route('/api/catalogs/<int:catalog_id>/unsubscribe', methods=['POST'])
@require_permission(Permission.CATALOG_SUBSCRIBE)
def unsubscribe(catalog_id):
    CatalogService.unsubscribe(current_org_id(), catalog_id)
    AuditService.record(
        'catalog.unsubscribe', actor=current_user(), org_id=current_org_id(),
        entity_type='catalog', entity_id=catalog_id,
    )
    db.session.commit()
    return jsonify({'ok': True})

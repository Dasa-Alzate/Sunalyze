
import logging
from flask import Blueprint, request, jsonify
from pydantic import ValidationError as PydanticValidationError

from app.extensions import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.wire import Wire
from app.models.catalog import Catalog
from app.models.provenance import ProvenanceMixin
from app.schemas.catalog import PanelSchema
from app.security import current_org_id
from app.authz import require_permission, Permission
from app.services.catalog_service import CatalogService
from app.services.equipment_import import EquipmentImportService
from app.services.audit_service import AuditService
from app.security import current_user
from app.db_helpers import commit_or_conflict
from app.errors import NotFound, Forbidden, ValidationError

logger = logging.getLogger(__name__)

crud_bp = Blueprint('crud', __name__)

RESOURCES = {
    'panels': {
        'model': Panel,
        'required': ['nombre', 'power', 'voc', 'vmp', 'imp'],
        'fields': ['nombre', 'y', 'tcp', 'tcv', 'voc', 'vmp', 'imp', 'isc',
                   'power', 't_noct', 'height', 'width', 'datasheet'],
        'numeric': ['y', 'tcp', 'tcv', 'voc', 'vmp', 'imp', 'isc', 'power', 't_noct'],
        'integer': ['height', 'width'],
        'defaults': {'y': 0, 'tcp': 0, 'tcv': 0, 'isc': 0, 't_noct': 45, 'height': 0, 'width': 0},
    },
    'inverters': {
        'model': Inverter,
        'required': ['nombre', 'power', 'vmax', 'I_max_input', 'I_max_output'],
        'fields': ['nombre', 'y', 'power_max', 'power', 'vmax',
                   'I_max_input', 'I_max_output', 'datasheet'],
        'numeric': ['y', 'power_max', 'power', 'vmax', 'I_max_input', 'I_max_output'],
        'integer': [],
        'defaults': {'y': 0},
    },
    'batteries': {
        'model': Battery,
        'required': ['nombre', 'capacity_kwh', 'power_kw', 'voltage'],
        'fields': ['nombre', 'capacity_kwh', 'usable_kwh', 'dod', 'power_kw', 'voltage',
                   'technology', 'round_trip_efficiency', 'max_cycles',
                   'height', 'width', 'depth', 'datasheet'],
        'numeric': ['capacity_kwh', 'usable_kwh', 'dod', 'power_kw', 'voltage',
                    'round_trip_efficiency'],
        'integer': ['max_cycles', 'height', 'width', 'depth'],
        'defaults': {},
    },
    'wires': {
        'model': Wire,
        'required': ['seccion', 'corriente', 'tipo', 'material', 'no_conductores'],
        'fields': ['seccion', 'corriente', 'tipo', 'material', 'no_conductores'],
        'numeric': ['seccion', 'corriente'],
        'integer': ['no_conductores'],
        'defaults': {},
    },
}

IMPORT_MAX_BYTES = 2 * 1024 * 1024

IMPORT_ALLOWED_EXTENSIONS = {'.csv', '.tsv', '.xlsx', '.xls'}

IMPORT_ALLOWED_MIMES = {
    'text/csv',
    'text/tab-separated-values',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

IMPORT_GENERIC_MIMES = {'application/octet-stream', 'text/plain', ''}


def _cfg(resource):
    return RESOURCES[resource]


def _import_extension(filename):
    name = (filename or '').lower()
    dot = name.rfind('.')
    return name[dot:] if dot != -1 else ''


def _validate_ranges(resource, values):
    if resource != 'panels':
        return
    payload = {k: v for k, v in values.items() if k in PanelSchema.model_fields}
    if not payload:
        return
    try:
        PanelSchema(**payload)
    except PydanticValidationError as exc:
        field = exc.errors()[0]['loc'][0] if exc.errors() else 'desconocido'
        raise ValidationError(f'Valor fuera de rango para el campo: {field}')


def _coerce(cfg, data):
    values = {}
    for field in cfg['fields']:
        if field not in data or data[field] in (None, ''):
            continue
        value = data[field]
        try:
            if field in cfg['numeric']:
                value = float(value)
            elif field in cfg['integer']:
                value = int(float(value))
        except (TypeError, ValueError):
            raise ValidationError(f'Campo numérico inválido: {field}')
        values[field] = value
    return values


def _official_catalog_ids():
    rows = db.session.query(Catalog.id).filter(
        Catalog.org_id.is_(None), Catalog.is_official.is_(True)
    ).all()
    return {r[0] for r in rows}


def _serialize(row, own_ids, official_ids=frozenset()):
    return {
        **row.to_dict(),
        'editable': row.catalog_id in own_ids or row.catalog_id in official_ids,
        'deletable': row.catalog_id in own_ids,
    }


def _visible_row(cfg, item_id, visible):
    row = cfg['model'].query.get(item_id)
    if not row or row.catalog_id not in visible:
        raise NotFound('Equipo no encontrado.')
    return row


def _editable_row(cfg, item_id, org_id, allow_official=False):
    visible = set(CatalogService.visible_catalog_ids(org_id))
    row = _visible_row(cfg, item_id, visible)
    if row.catalog_id in set(CatalogService.own_catalog_ids(org_id)):
        return row
    if allow_official and row.catalog_id in _official_catalog_ids():
        return row
    raise Forbidden('Los equipos del marketplace no se pueden modificar. Crea una copia en tu catálogo.')


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>', methods=['GET'])
@require_permission(Permission.EQUIPMENT_VIEW)
def list_equipment(resource):
    cfg = _cfg(resource)
    org_id = current_org_id()
    visible = CatalogService.visible_catalog_ids(org_id)
    own_ids = set(CatalogService.own_catalog_ids(org_id))
    official_ids = _official_catalog_ids()
    query = cfg['model'].query.filter(cfg['model'].catalog_id.in_(visible))
    catalog_id = request.args.get('catalog_id', type=int)
    if catalog_id:
        query = query.filter(cfg['model'].catalog_id == catalog_id)
    return jsonify([_serialize(r, own_ids, official_ids) for r in query.all()])


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>', methods=['GET'])
@require_permission(Permission.EQUIPMENT_VIEW)
def get_equipment(resource, item_id):
    cfg = _cfg(resource)
    org_id = current_org_id()
    visible = set(CatalogService.visible_catalog_ids(org_id))
    row = _visible_row(cfg, item_id, visible)
    return jsonify(_serialize(row, set(CatalogService.own_catalog_ids(org_id)), _official_catalog_ids()))


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>', methods=['POST'])
@require_permission(Permission.EQUIPMENT_EDIT)
def create_equipment(resource):
    cfg = _cfg(resource)
    org_id = current_org_id()
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.')
    missing = [f for f in cfg['required'] if data.get(f) in (None, '')]
    if missing:
        raise ValidationError('Campos requeridos: ' + ', '.join(missing))

    catalog = CatalogService.resolve_target_catalog(org_id, data.get('catalog_id'))
    coerced = _coerce(cfg, data)
    _validate_ranges(resource, coerced)
    values = {**cfg['defaults'], **coerced}
    row = cfg['model'](**values, catalog_id=catalog.id)
    if resource == 'inverters' and row.power_max is None:
        row.power_max = row.power
    db.session.add(row)
    db.session.flush()
    AuditService.record(
        'equipment.create', actor=current_user(), org_id=org_id,
        entity_type=resource, entity_id=row.id,
        payload={'resource': resource, 'nombre': data.get('nombre'),
                 'catalog_id': catalog.id},
    )
    commit_or_conflict('Ya existe un equipo con ese nombre.')
    return jsonify(_serialize(row, {catalog.id})), 201


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>/import', methods=['POST'])
@require_permission(Permission.EQUIPMENT_EDIT)
def import_equipment(resource):
    cfg = _cfg(resource)
    org_id = current_org_id()
    uploaded = request.files.get('file')
    if uploaded is None or not uploaded.filename:
        raise ValidationError('Adjunta un archivo en el campo «file».', code='import.no_file')

    extension = _import_extension(uploaded.filename)
    if extension not in IMPORT_ALLOWED_EXTENSIONS:
        raise ValidationError(
            'Formato no admitido. Usa TSV, CSV o Excel.', code='import.bad_extension')
    mimetype = (uploaded.mimetype or '').lower()
    if mimetype not in IMPORT_ALLOWED_MIMES and mimetype not in IMPORT_GENERIC_MIMES:
        raise ValidationError(
            'Tipo de contenido no admitido.', code='import.bad_mime')

    content = uploaded.read()
    if not content:
        raise ValidationError('El archivo está vacío.', code='import.empty')
    if len(content) > IMPORT_MAX_BYTES:
        raise ValidationError(
            'El archivo supera el límite de 2 MB.', code='import.too_large')

    catalog_id = request.form.get('catalog_id', type=int)
    summary = EquipmentImportService.run(
        resource, cfg, org_id, uploaded.filename, content, catalog_id=catalog_id)
    AuditService.record(
        'equipment.import', actor=current_user(), org_id=org_id,
        entity_type='catalog', entity_id=summary.get('catalog_id'),
        payload={'resource': resource, 'created': summary['created'],
                 'updated': summary['updated'], 'errors': len(summary['errors'])},
    )
    db.session.commit()
    return jsonify(summary)


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>', methods=['PATCH'])
@require_permission(Permission.EQUIPMENT_EDIT)
def update_equipment(resource, item_id):
    cfg = _cfg(resource)
    org_id = current_org_id()
    row = _editable_row(cfg, item_id, org_id, allow_official=True)
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.')
    coerced = _coerce(cfg, data)
    _validate_ranges(resource, coerced)
    for field, value in coerced.items():
        setattr(row, field, value)
    if data.get('catalog_id') and data['catalog_id'] != row.catalog_id:
        target = CatalogService.resolve_target_catalog(org_id, data['catalog_id'])
        row.catalog_id = target.id
    if isinstance(row, ProvenanceMixin):
        row.is_locked = True
        row.source = 'manual'
        row.needs_review = False
    AuditService.record(
        'equipment.update', actor=current_user(), org_id=org_id,
        entity_type=resource, entity_id=row.id,
        payload={'resource': resource, 'nombre': getattr(row, 'nombre', None),
                 'catalog_id': row.catalog_id},
    )
    db.session.commit()
    return jsonify(_serialize(row, set(CatalogService.own_catalog_ids(org_id)), _official_catalog_ids()))


@crud_bp.route('/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>', methods=['DELETE'])
@require_permission(Permission.EQUIPMENT_EDIT)
def delete_equipment(resource, item_id):
    cfg = _cfg(resource)
    org_id = current_org_id()
    row = _editable_row(cfg, item_id, org_id)
    nombre = getattr(row, 'nombre', None)
    catalog_id = row.catalog_id
    db.session.delete(row)
    AuditService.record(
        'equipment.delete', actor=current_user(), org_id=org_id,
        entity_type=resource, entity_id=item_id,
        payload={'resource': resource, 'nombre': nombre, 'catalog_id': catalog_id},
    )
    db.session.commit()
    return jsonify({'message': 'Equipo eliminado correctamente'})


@crud_bp.route('/api/wires/search', methods=['GET'])
@require_permission(Permission.EQUIPMENT_VIEW)
def search_wires():
    visible = CatalogService.visible_catalog_ids(current_org_id())
    query = Wire.query.filter(Wire.catalog_id.in_(visible))

    material = request.args.get('material')
    tipo = request.args.get('tipo')
    min_corriente = request.args.get('min_corriente')
    max_seccion = request.args.get('max_seccion')
    no_conductores = request.args.get('no_conductores')

    if material:
        query = query.filter(Wire.material == material)
    if tipo:
        query = query.filter(Wire.tipo == tipo)
    if min_corriente:
        query = query.filter(Wire.corriente >= float(min_corriente))
    if max_seccion:
        query = query.filter(Wire.seccion <= float(max_seccion))
    if no_conductores:
        query = query.filter(Wire.no_conductores == int(no_conductores))

    return jsonify([w.to_dict() for w in query.all()])


@crud_bp.route('/api/wires/calculate-section', methods=['POST'])
@require_permission(Permission.EQUIPMENT_VIEW)
def calculate_section():
    data = request.get_json(silent=True)
    if not data:
        raise ValidationError('Cuerpo JSON requerido.')
    required = ['tipo', 'material', 'no_conductores', 'i_section']
    missing = [f for f in required if f not in data]
    if missing:
        raise ValidationError('Campos requeridos: ' + ', '.join(missing))

    visible = CatalogService.visible_catalog_ids(current_org_id())
    wires = Wire.query.filter(
        Wire.catalog_id.in_(visible),
        Wire.tipo == data['tipo'],
        Wire.material == data['material'],
        Wire.no_conductores == int(data['no_conductores']),
        Wire.corriente >= float(data['i_section']) * 1.25,
        Wire.seccion >= 6,
    ).order_by(Wire.corriente.asc()).all()

    if not wires:
        raise NotFound('No se encontraron cables que cumplan los criterios.')

    wire = wires[0]
    return jsonify({'seccion': wire.seccion, 'corriente': wire.corriente, 'wire': wire.to_dict()})

"""Endpoints del constructor de plantillas de documentos. Capa HTTP fina.

Todas las rutas van detrás del flag `templates` (@require_flag) y de un permiso RBAC. La
lectura exige TEMPLATE_VIEW; la escritura, TEMPLATE_MANAGE (owner+admin). El alcance por
org_id se aplica en TemplateService (sin IDOR).
"""

from flask import Blueprint, request, jsonify

from app.security import current_org_id, current_user
from app.authz import require_permission, require_flag, Permission
from app.services.template_service import TemplateService
from app.services.template_engine import variable_catalog
from app.schemas.templates import (
    TemplateCreateSchema, TemplateUpdateSchema, ContentSchema, PreviewSchema,
    CategorySchema, LabelSchema, FavoriteSchema, CategoryAssignSchema, LabelsAssignSchema,
)

templates_bp = Blueprint('templates', __name__)

FLAG = 'templates'


def _body():
    return request.get_json(silent=True) or {}


@templates_bp.route('/api/templates', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_templates():
    return jsonify(TemplateService.list_org_templates(
        current_org_id(), kind=request.args.get('kind')))


@templates_bp.route('/api/templates/bank', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_bank():
    return jsonify(TemplateService.list_system_bank(kind=request.args.get('kind')))


@templates_bp.route('/api/templates/variables/<kind>', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_variables(kind):
    return jsonify(variable_catalog(kind))


@templates_bp.route('/api/templates/<int:template_id>', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def get_template(template_id):
    return jsonify(TemplateService.get_template(current_org_id(), template_id))


@templates_bp.route('/api/templates', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def create_template():
    data = TemplateCreateSchema(**_body())
    user = current_user()
    tpl = TemplateService.create_template(
        current_org_id(), user.id if user else None, data.kind, data.name,
        description=data.description, country=data.country, region=data.region,
        content=data.content,
    )
    return jsonify(tpl.to_dict(with_content=True)), 201


@templates_bp.route('/api/templates/<int:template_id>', methods=['PATCH'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def update_template(template_id):
    data = TemplateUpdateSchema(**_body())
    tpl = TemplateService.update_template(
        current_org_id(), template_id, **data.model_dump(exclude_none=True))
    return jsonify(tpl.to_dict())


@templates_bp.route('/api/templates/<int:template_id>', methods=['DELETE'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def delete_template(template_id):
    TemplateService.delete_template(current_org_id(), template_id)
    return jsonify({'ok': True})


@templates_bp.route('/api/templates/<int:template_id>/content', methods=['PUT'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def save_content(template_id):
    data = ContentSchema(**_body())
    version = TemplateService.save_content(
        current_org_id(), template_id, data.content, changelog=data.changelog)
    return jsonify(version.to_dict())


@templates_bp.route('/api/templates/<int:template_id>/publish', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def publish_template(template_id):
    tpl = TemplateService.publish(current_org_id(), template_id)
    return jsonify(tpl.to_dict())


@templates_bp.route('/api/templates/<int:template_id>/preview', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def preview_template(template_id):
    data = PreviewSchema(**_body())
    result = TemplateService.preview(
        current_org_id(), template_id, data.project_id, user=current_user())
    return jsonify(result)


@templates_bp.route('/api/templates/library', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_library():
    favorite = request.args.get('favorite')
    favorite = (favorite.lower() == 'true') if favorite is not None else None
    category_id = request.args.get('category_id', type=int)
    return jsonify(TemplateService.list_library(
        current_org_id(), favorite=favorite, category_id=category_id))


@templates_bp.route('/api/templates/<int:template_id>/install', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def install_template(template_id):
    inst = TemplateService.install(current_org_id(), template_id)
    return jsonify(inst.to_dict()), 201


@templates_bp.route('/api/templates/library/<int:installation_id>', methods=['DELETE'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def uninstall_template(installation_id):
    TemplateService.uninstall(current_org_id(), installation_id)
    return jsonify({'ok': True})


@templates_bp.route('/api/templates/library/<int:installation_id>/favorite', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def favorite_installation(installation_id):
    data = FavoriteSchema(**_body())
    inst = TemplateService.set_favorite(current_org_id(), installation_id, data.is_favorite)
    return jsonify(inst.to_dict())


@templates_bp.route('/api/templates/library/<int:installation_id>/category', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def categorize_installation(installation_id):
    data = CategoryAssignSchema(**_body())
    inst = TemplateService.set_category(current_org_id(), installation_id, data.category_id)
    return jsonify(inst.to_dict())


@templates_bp.route('/api/templates/library/<int:installation_id>/labels', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def label_installation(installation_id):
    data = LabelsAssignSchema(**_body())
    inst = TemplateService.set_labels(current_org_id(), installation_id, data.label_ids)
    return jsonify(inst.to_dict())


@templates_bp.route('/api/templates/categories', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_categories():
    return jsonify(TemplateService.list_categories(current_org_id()))


@templates_bp.route('/api/templates/categories', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def create_category():
    data = CategorySchema(**_body())
    category = TemplateService.create_category(current_org_id(), data.name)
    return jsonify(category.to_dict()), 201


@templates_bp.route('/api/templates/categories/<int:category_id>', methods=['DELETE'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def delete_category(category_id):
    TemplateService.delete_category(current_org_id(), category_id)
    return jsonify({'ok': True})


@templates_bp.route('/api/templates/labels', methods=['GET'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_VIEW)
def list_labels():
    return jsonify(TemplateService.list_labels(current_org_id()))


@templates_bp.route('/api/templates/labels', methods=['POST'])
@require_flag(FLAG)
@require_permission(Permission.TEMPLATE_MANAGE)
def create_label():
    data = LabelSchema(**_body())
    label = TemplateService.create_label(current_org_id(), data.name)
    return jsonify(label.to_dict()), 201

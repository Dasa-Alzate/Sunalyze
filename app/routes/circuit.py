
from flask import Blueprint, jsonify, request, Response

from app.services.circuit_diagram_service import CircuitDiagramService
from app.schemas.circuit import CircuitConfigSchema

circuit_bp = Blueprint('circuit', __name__, url_prefix='/api/circuit')


def _validate_args(args):
    sent = {
        k: v for k, v in args.items()
        if k in CircuitConfigSchema.model_fields and str(v).strip() != ''
    }
    CircuitConfigSchema(**sent)


@circuit_bp.route('/templates')
def get_templates():
    return jsonify(CircuitDiagramService.list_templates())


@circuit_bp.route('/<string:diagram_type>')
def get_diagram(diagram_type):
    args = request.args.to_dict()
    _validate_args(args)
    svg = CircuitDiagramService.generate(diagram_type, args)
    return Response(svg, mimetype='image/svg+xml')

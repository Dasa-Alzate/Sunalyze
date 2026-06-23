"""Endpoint de diagramas unifilares SVG. HTTP fino sobre CircuitDiagramService."""

from flask import Blueprint, jsonify, request, Response

from app.services.circuit_diagram_service import CircuitDiagramService

circuit_bp = Blueprint('circuit', __name__, url_prefix='/api/circuit')


@circuit_bp.route('/templates')
def get_templates():
    return jsonify(CircuitDiagramService.list_templates())


@circuit_bp.route('/<string:diagram_type>')
def get_diagram(diagram_type):
    svg = CircuitDiagramService.generate(diagram_type, request.args.to_dict())
    return Response(svg, mimetype='image/svg+xml')

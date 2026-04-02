"""Circuit diagram routes."""

from flask import Blueprint, request
from app.controllers.circuit_controller import CircuitController

circuit_bp = Blueprint('circuit', __name__, url_prefix='/api/circuit')


@circuit_bp.route('/<string:diagram_type>')
def get_diagram(diagram_type: str):
    """
    Generate a circuit unifilar diagram as SVG.

    GET /api/circuit/cc  — DC-side unifilar (campo FV → inversor)
    GET /api/circuit/ca  — AC-side unifilar (inversor → red)

    Query parameters: see CircuitController.REQUIRED_FIELDS
    """
    return CircuitController.generate(diagram_type, request.args.to_dict())

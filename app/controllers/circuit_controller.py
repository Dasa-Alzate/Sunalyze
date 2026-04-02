"""Controller for circuit diagram generation endpoints."""

from flask import jsonify, Response
from app.services.circuit import CircuitService


class CircuitController:
    """Handles validation, data mapping and SVG generation for circuit diagrams."""

    REQUIRED_FIELDS = [
        'panel_model', 'panel_voc', 'panel_isc',
        'panels_per_string', 'num_strings',
        'dc_fuse_i', 'dc_switch_v', 'dc_cable_section',
    ]

    GENERATORS = {
        'cc-strings': CircuitService.generate_cc_vertical,
    }

    @staticmethod
    def generate(diagram_type: str, data: dict):
        """
        Validate input, build config and return the SVG response.

        Args:
            diagram_type: 'cc' | 'ca' | 'cc-strings' | 'red' | 'sistema'
            data: Flat dict from request.args or request.get_json().

        Returns:
            Flask Response with SVG or JSON error.
        """
        if diagram_type not in CircuitController.GENERATORS:
            valid = ", ".join(CircuitController.GENERATORS)
            return jsonify({'error': f"Tipo desconocido: '{diagram_type}'. Válidos: {valid}"}), 400

        missing = [f for f in CircuitController.REQUIRED_FIELDS if not str(data.get(f, '')).strip()]
        if missing:
            return jsonify({'error': 'Parámetros obligatorios ausentes', 'fields': missing}), 400

        config = CircuitService.config_from_dict(data)
        generator = CircuitController.GENERATORS[diagram_type]
        svg = generator(config)

        return Response(svg, mimetype='image/svg+xml')

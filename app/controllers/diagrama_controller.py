"""Controlador para la generación de diagramas funcionales."""

import logging
from flask import render_template, jsonify
from app.models.panel import Panel
from app.models.inverter import Inverter

logger = logging.getLogger(__name__)


class DiagramaController:
    """Controlador para el diagrama funcional de la instalación fotovoltaica."""

    @staticmethod
    def get_diagrama_completo(data):
        """
        Valida los datos de entrada y renderiza el diagrama funcional.

        Args:
            data: dict con panel_id, inverter_id y parámetros del campo solar.

        Returns:
            HTML renderizado o respuesta de error JSON.
        """
        try:
            if not data or data.get('panel_id') in (None, ''):
                return jsonify({"error": "El campo 'panel_id' es requerido."}), 400
            if data.get('inverter_id') in (None, ''):
                return jsonify({"error": "El campo 'inverter_id' es requerido."}), 400

            panel = Panel.query.get(data['panel_id'])
            if not panel:
                return jsonify({"error": "Panel no encontrado"}), 400

            inverter = Inverter.query.get(data['inverter_id'])
            if not inverter:
                return jsonify({"error": "Inversor no encontrado"}), 400

            return render_template(
                'diagrama_funcional.html',
                panel=panel,
                inverter=inverter,
                field_power=data.get('field_power', '0'),
                panel_amount=data.get('panel_amount', '0'),
                needed_surface=data.get('needed_surface', '0'),
                beta_optimal=data.get('beta_optimal', '0'),
                max_panels_per_string=data.get('max_panels_per_string', '0'),
                total_yield=data.get('total_yield', '0'),
                first_section=data.get('first_section', '2x60mm²'),
                second_section=data.get('second_section', '2x60mm²'),
                first_length=data.get('first_length', ''),
                second_length=data.get('second_length', ''),
                panel_protection_v=data.get('panel_protection_v', ''),
                panel_protection_i=data.get('panel_protection_i', ''),
            )

        except Exception:
            logger.exception("Error en get_diagrama_completo")
            return jsonify({"error": "Error interno del servidor"}), 500

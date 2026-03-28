"""Controlador para la generación de la memoria técnica en PDF."""

from flask import render_template, jsonify, Response
from weasyprint import HTML
from app.models.panel import Panel
from app.models.inverter import Inverter


class MemoriaController:
    """Controlador para la generación de la memoria técnica fotovoltaica en PDF."""

    REQUIRED_FIELDS = [
        'location', 'client_name', 'address', 'zipcode', 'catastral_reference',
        'energy_company_name', 'energy_company_cups', 'hired_power_kw', 'input_v',
        'input_v_type', 'inyection_type', 'panels_peak_power_kw', 'panels_number',
        'panels_place', 'panels_disposition', 'inverter_place',
        'wire_dc_material', 'wire_dc_model', 'wire_dc_type',
        'wire_ac_material', 'wire_ac_model', 'wire_ac_type',
        'wire_ground_material', 'wire_ground_length',
        'protections_dc_thermal_v_max', 'protections_dc_thermal_model',
        'protections_dc_breaker_i', 'protections_dc_breaker_model',
        'protections_dc_surge_model', 'protections_ac_thermal_i',
        'protections_ac_thermal_model', 'protections_ac_diff_i',
        'protections_ac_diff_model', 'protections_ac_transitory_surge_model',
        'zero_inyection_model', 'metering_device_model', 'mppt_inputs',
    ]

    @staticmethod
    def generar_pdf(form_data):
        """
        Valida el formulario, construye las variables de plantilla y devuelve
        la memoria técnica como PDF.

        Args:
            form_data: ImmutableMultiDict del request.form (POST) o dict vacío (GET).

        Returns:
            Flask Response con el PDF o respuesta de error JSON.
        """
        template_vars = {}

        if form_data:
            missing = [f for f in MemoriaController.REQUIRED_FIELDS if not form_data.get(f, '').strip()]
            if missing:
                return jsonify({'error': 'Campos obligatorios vacíos', 'fields': missing}), 400

            panel = Panel.query.get(form_data.get('panel_id'))
            inverter = Inverter.query.get(form_data.get('inverter_id'))

            if not panel or not inverter:
                return jsonify({'error': 'Panel o inversor no encontrado'}), 400

            template_vars = MemoriaController._build_template_vars(form_data, panel, inverter)

        html_string = render_template('memoria_tecnica_pdf.html', **template_vars)
        pdf = HTML(string=html_string).write_pdf()

        return Response(
            pdf,
            mimetype='application/pdf',
            headers={'Content-Disposition': 'inline; filename=memoria_tecnica.pdf'}
        )

    @staticmethod
    def _build_template_vars(data, panel, inverter):
        """Construye el dict de variables para la plantilla PDF."""
        return {
            'client_name': data.get('client_name'),
            'address': data.get('address'),
            'zipcode': data.get('zipcode'),
            'catastral_reference': data.get('catastral_reference'),
            'energy_company_name': data.get('energy_company_name'),
            'energy_company_cups': data.get('energy_company_cups'),
            'hired_power_kw': data.get('hired_power_kw'),
            'input_v': data.get('input_v'),
            'input_v_type': data.get('input_v_type'),
            'inyection_type': data.get('inyection_type'),
            'panels_inclination_verbosed': data.get('panels_inclination_verbosed'),
            'panels_azimut_verbosed': data.get('panels_azimut_verbosed'),
            'panels_peak_power_kw': data.get('panels_peak_power_kw'),
            'panels_number': data.get('panels_number'),
            'panels_place': data.get('panels_place'),
            'panels_disposition': data.get('panels_disposition'),
            'panels_surface': data.get('panels_surface'),
            'panels_inclination': data.get('panels_inclination'),
            'panels_azimut': data.get('panels_azimut'),
            'orientation_loss_verbosed': data.get('orientation_loss_verbosed'),
            'shadows_loss_verbosed': data.get('shadows_loss_verbosed'),
            'panel_temp_min_limit': data.get('panel_temp_min_limit'),
            'panel_temp_max_limit': data.get('panel_temp_max_limit'),
            'anti_pouring_verbosed': data.get('anti_pouring_verbosed'),
            'batteries_verbosed': data.get('batteries_verbosed'),
            'panels_model': panel.nombre,
            'panels_power': panel.power,
            'panels_width': panel.width,
            'panels_height': panel.height,
            'panels_voc': panel.voc,
            'panels_isc': panel.isc,
            'panels_vmp': panel.vmp,
            'panels_imp': panel.imp,
            'panels_efficiency': panel.y,
            'panels_tcp': panel.tcp,
            'panels_tcv': panel.tcv,
            'inverter_model': inverter.nombre,
            'inverter_nominal_power': inverter.power,
            'inverter_vmax': inverter.vmax,
            'inverter_i_max_input': inverter.I_max_input,
            'inverter_i_max_output': inverter.I_max_output,
            'inverter_efficiency': inverter.y,
            'inverter_phases': data.get('inverter_phases'),
            'inverter_place': data.get('inverter_place'),
            'wire_dc_material': data.get('wire_dc_material'),
            'wire_dc_length': data.get('wire_dc_length'),
            'wire_dc_section': data.get('wire_dc_section'),
            'wire_dc_model': data.get('wire_dc_model'),
            'wire_dc_type': data.get('wire_dc_type'),
            'wire_ac_material': data.get('wire_ac_material'),
            'wire_ac_length': data.get('wire_ac_length'),
            'wire_ac_section': data.get('wire_ac_section'),
            'wire_ac_model': data.get('wire_ac_model'),
            'wire_ac_type': data.get('wire_ac_type'),
            'wire_ground_material': data.get('wire_ground_material'),
            'wire_ground_length': data.get('wire_ground_length'),
            'wire_ground_section': data.get('wire_ground_section'),
            'protections_dc_thermal_v_max': data.get('protections_dc_thermal_v_max'),
            'protections_dc_thermal_model': data.get('protections_dc_thermal_model'),
            'protections_dc_breaker_i': data.get('protections_dc_breaker_i'),
            'protections_dc_breaker_model': data.get('protections_dc_breaker_model'),
            'protections_dc_surge_model': data.get('protections_dc_surge_model'),
            'protections_ac_thermal_i': data.get('protections_ac_thermal_i'),
            'protections_ac_thermal_model': data.get('protections_ac_thermal_model'),
            'protections_ac_diff_i': data.get('protections_ac_diff_i'),
            'protections_ac_diff_model': data.get('protections_ac_diff_model'),
            'protections_ac_transitory_surge_model': data.get('protections_ac_transitory_surge_model'),
            'zero_inyection_model': data.get('zero_inyection_model'),
            'metering_device_model': data.get('metering_device_model'),
            'mppt_inputs': data.get('mppt_inputs'),
            'panels_output_i_max_expected': data.get('panels_output_i_max_expected'),
            'panels_output_i_max_oversized': data.get('panels_output_i_max_oversized'),
            'inverter_output_i_max_expected': data.get('inverter_output_i_max_expected'),
            'location': data.get('location'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'altitude': data.get('altitude'),
            'annual_production': data.get('annual_production'),
            'annual_irradiance': data.get('annual_irradiance'),
            'date': data.get('date'),
        }

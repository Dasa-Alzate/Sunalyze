"""Generacion de la memoria tecnica en PDF: dominio, sin HTTP.

Devuelve los bytes del PDF; el route decide cabeceras y Response. Usa el
renderizado Jinja de Flask como motor de plantillas (no toca request).
WeasyPrint/pikepdf se importan de forma diferida: solo se exigen al generar.
"""

import io
import json
import logging
import os
from flask import render_template

from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.installation_defaults import InstallationDefaults
from app.services.circuit import CircuitService, DCConfig, ACConfig, SystemConfig
from app.services.graph_service import GraphService
from app.errors import ValidationError, NotFound, DomainError

logger = logging.getLogger(__name__)

DATASHEETS_DIR = os.path.join(os.path.dirname(__file__), '../../data/datasheets')


def _safe_datasheet_path(name):
    """Resuelve `name` dentro de `DATASHEETS_DIR` o devuelve `None` si es inseguro.

    Rechaza separadores de ruta y componentes `..`, y exige que el `realpath`
    quede bajo `DATASHEETS_DIR` (cierra el path traversal en los datasheets).
    """
    if not name or os.path.sep in name or (os.path.altsep and os.path.altsep in name) or '..' in name:
        return None
    root = os.path.realpath(DATASHEETS_DIR)
    real = os.path.realpath(os.path.join(root, name))
    if real == root or not real.startswith(root + os.sep):
        return None
    return real


class MemoriaService:

    REQUIRED_FIELDS = [
        'location', 'client_name', 'address', 'zipcode', 'catastral_reference',
        'energy_company_name', 'energy_company_cups', 'hired_power_kw', 'input_v',
        'input_v_type', 'inyection_type', 'panels_peak_power_kw', 'panels_number',
        'panels_place', 'panels_disposition', 'inverter_place',
        'wire_ground_length',
        'protections_dc_thermal_v_max', 'protections_dc_breaker_i',
        'protections_ac_thermal_i', 'protections_ac_diff_i',
        'protections_ac_transitory_surge_model', 'mppt_inputs',
    ]

    @staticmethod
    def generar_pdf(form_data):
        from weasyprint import HTML
        from flask import current_app
        from app.services.pdf_url_fetcher import restricted_url_fetcher

        template_vars = {}
        panel = inverter = None

        if form_data:
            missing = [f for f in MemoriaService.REQUIRED_FIELDS if not form_data.get(f, '').strip()]
            if missing:
                raise ValidationError('Campos obligatorios vacíos', details={'fields': missing})

            panel = Panel.query.get(form_data.get('panel_id'))
            inverter = Inverter.query.get(form_data.get('inverter_id'))
            defaults = InstallationDefaults.get()

            if not panel or not inverter:
                raise NotFound('Panel o inversor no encontrado')
            if not defaults:
                raise DomainError('Configuración de instalación no encontrada', status_code=500)

            battery = None
            if form_data.get('battery_id'):
                battery = Battery.query.get(form_data.get('battery_id'))

            template_vars = MemoriaService._build_template_vars(form_data, panel, inverter, defaults)
            template_vars.update(MemoriaService._build_battery_vars(form_data, battery))
            template_vars.update(MemoriaService._build_circuit_svgs(form_data, panel, inverter, battery))
            template_vars.update(MemoriaService._build_graph_svgs(form_data))

        html_string = render_template('memoria_tecnica_pdf.html', **template_vars)
        memoria_pdf = HTML(
            string=html_string,
            base_url=current_app.instance_path,
            url_fetcher=restricted_url_fetcher,
        ).write_pdf()

        datasheets = MemoriaService._collect_datasheets(panel, inverter) if form_data else []
        return MemoriaService._merge_pdfs(memoria_pdf, datasheets)

    @staticmethod
    def _build_template_vars(data, panel, inverter, defaults):
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
            'wire_dc_material': defaults.dc_material,
            'wire_dc_length': data.get('wire_dc_length'),
            'wire_dc_section': data.get('wire_dc_section'),
            'wire_dc_model': defaults.dc_modelo,
            'wire_ac_material': defaults.ac_material,
            'wire_ac_length': data.get('wire_ac_length'),
            'wire_ac_section': data.get('wire_ac_section'),
            'wire_ac_model': defaults.ac_modelo,
            'wire_ground_material': defaults.tierra_material,
            'wire_ground_model': defaults.tierra_modelo,
            'wire_ground_length': data.get('wire_ground_length'),
            'wire_ground_section': data.get('wire_ground_section'),
            'protections_dc_thermal_v_max': data.get('protections_dc_thermal_v_max'),
            'protections_dc_thermal_model': defaults.dc_magnetotermico_modelo,
            'protections_dc_breaker_i': data.get('protections_dc_breaker_i'),
            'protections_dc_breaker_model': defaults.dc_fusibles_modelo,
            'protections_dc_portafusibles': defaults.dc_portafusibles,
            'protections_dc_surge_model': defaults.dc_sobretensiones_modelo,
            'protections_ac_thermal_i': data.get('protections_ac_thermal_i'),
            'protections_ac_thermal_model': defaults.ac_magnetotermico_modelo,
            'protections_ac_diff_i': data.get('protections_ac_diff_i'),
            'protections_ac_diff_model': defaults.ac_diferencial_modelo,
            'protections_ac_transitory_surge_model': data.get('protections_ac_transitory_surge_model'),
            'zero_inyection_model': defaults.inyeccion_cero_modelo,
            'metering_device_model': defaults.dispositivo_medida_modelo,
            'mppt_inputs': data.get('mppt_inputs'),
            'panels_output_i_max_expected': data.get('panels_output_i_max_expected'),
            'panels_output_i_max_oversized': data.get('panels_output_i_max_oversized'),
            'inverter_output_i_max_expected': data.get('inverter_output_i_max_expected'),
            'is_coplanar': data.get('is_coplanar') == '1',
            'location': data.get('location'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'altitude': data.get('altitude'),
            'annual_production': data.get('annual_production'),
            'annual_irradiance': data.get('annual_irradiance'),
            'date': data.get('date'),
        }

    @staticmethod
    def _build_battery_vars(data, battery):
        try:
            battery_quantity = max(1, int(data.get('battery_quantity') or 1))
        except (TypeError, ValueError):
            battery_quantity = 1
        if not battery:
            return {
                'has_battery': False,
                'battery_quantity': battery_quantity,
            }
        return {
            'has_battery': True,
            'battery_quantity': battery_quantity,
            'battery_model': battery.nombre,
            'battery_capacity_kwh': battery.capacity_kwh,
            'battery_usable_kwh': battery.usable_kwh,
            'battery_dod': battery.dod,
            'battery_power_kw': battery.power_kw,
            'battery_voltage': battery.voltage,
            'battery_technology': battery.technology,
            'battery_round_trip_efficiency': battery.round_trip_efficiency,
            'battery_max_cycles': battery.max_cycles,
        }

    @staticmethod
    def _build_circuit_svgs(data, panel, inverter, battery=None):
        def _f(key, default=0.0):
            try:
                return float(data.get(key) or default)
            except (ValueError, TypeError):
                return default

        def _i(key, default=1):
            try:
                return int(data.get(key) or default)
            except (ValueError, TypeError):
                return default

        try:
            num_strings = _i('mppt_inputs', 1)
            panels_number = _i('panels_number', num_strings)
            panels_per_string = max(1, round(panels_number / num_strings))

            dc = DCConfig(
                panel_model=panel.nombre,
                panel_voc=float(panel.voc),
                panel_isc=float(panel.isc),
                panels_per_string=panels_per_string,
                num_strings=num_strings,
                fuse_i=_f('protections_dc_breaker_i', round(float(panel.isc) * 1.25, 1)),
                switch_v=_f('protections_dc_thermal_v_max', float(panel.voc) * panels_per_string * 1.25),
                cable_section=data.get('wire_dc_section') or data.get('wire_dc_model') or '6 mm²',
            )

            phases_raw = data.get('inverter_phases', '1')
            phases = 3 if str(phases_raw).strip() in ('3', 'trifásico', 'trifasico') else 1

            ac = ACConfig(
                inverter_model=inverter.nombre,
                inverter_power=float(inverter.power),
                inverter_output_i=float(inverter.I_max_output),
                phases=phases,
                mcb_i=_f('protections_ac_thermal_i', round(float(inverter.I_max_output) * 1.25, 1)),
                rcd_i=_f('protections_ac_diff_i', 25.0),
                rcd_sensitivity=data.get('protections_ac_diff_sensitivity') or '30 mA',
                cable_section=data.get('wire_ac_section') or data.get('wire_ac_model') or '6 mm²',
                has_zero_injection=bool(data.get('zero_inyection_model')),
                zero_injection_model=data.get('zero_inyection_model') or '',
                has_battery=battery is not None,
                battery_model=battery.nombre if battery else '',
            )

            config = SystemConfig(dc=dc, ac=ac)

            return {
                'svg_ca': CircuitService.generate_grid_connection(config),
                'svg_cc': CircuitService.generate_cc_vertical(config),
                'svg_sistema': CircuitService.generate_full_system(config),
            }

        except Exception:
            logger.exception('Error generando diagramas SVG para la memoria')
            empty = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="80"><text x="10" y="40" font-family="monospace" font-size="12" fill="#888">Diagrama no disponible</text></svg>'
            return {'svg_ca': empty, 'svg_cc': empty, 'svg_sistema': empty}

    @staticmethod
    def _build_graph_svgs(data):
        try:
            monthly_production = json.loads(data.get('monthly_production', '[]'))
            monthly_irradiance = json.loads(data.get('monthly_irradiance', '[]'))
        except (json.JSONDecodeError, TypeError):
            monthly_production = []
            monthly_irradiance = []

        result = {}
        if monthly_production:
            result['svg_production'] = GraphService.generate_monthly_production(monthly_production)
        if monthly_irradiance:
            result['svg_irradiance'] = GraphService.generate_monthly_irradiance(monthly_irradiance)
        try:
            annual_consumption = float(data.get('annual_consumption', 0))
        except (ValueError, TypeError):
            annual_consumption = 0
        if monthly_production and annual_consumption > 0:
            result['svg_balance'] = GraphService.generate_energy_balance(monthly_production, annual_consumption)
        return result

    @staticmethod
    def _collect_datasheets(panel, inverter):
        paths = []
        for device in (panel, inverter):
            if device.datasheet:
                path = _safe_datasheet_path(device.datasheet)
                if path is None:
                    logger.warning('Datasheet con ruta insegura, ignorado: %s', device.datasheet)
                elif os.path.isfile(path):
                    paths.append(path)
                else:
                    logger.warning('Datasheet no encontrado: %s', path)
        return paths

    @staticmethod
    def _merge_pdfs(memoria_bytes, datasheet_paths):
        if not datasheet_paths:
            return memoria_bytes

        import pikepdf

        output = pikepdf.Pdf.new()
        memoria = pikepdf.Pdf.open(io.BytesIO(memoria_bytes))
        output.pages.extend(memoria.pages)

        root = os.path.realpath(DATASHEETS_DIR)
        for path in datasheet_paths:
            real = os.path.realpath(path)
            if not real.startswith(root + os.sep):
                logger.warning('Datasheet fuera del arbol permitido, ignorado: %s', path)
                continue
            try:
                ds = pikepdf.Pdf.open(real)
                output.pages.extend(ds.pages)
            except Exception:
                logger.exception('Error adjuntando datasheet: %s', path)

        buf = io.BytesIO()
        output.save(buf)
        return buf.getvalue()

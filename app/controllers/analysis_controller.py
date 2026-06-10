"""Controlador principal de analisis fotovoltaico."""

from flask import jsonify
import pvlib
import math
import logging
from app.models.panel import Panel
from app.models.inverter import Inverter

logger = logging.getLogger(__name__)

DIRTY_LOSS = 0.97
WIRES_LOSS = 0.985
OPERATION_TEMP_CELL = 50

class AnalysisController:
    """
    Controlador para el dimensionamiento de instalaciones fotovoltaicas.

    Utiliza datos de irradiancia de PVGIS y especificaciones tecnicas de paneles
    e inversores para calcular el numero de paneles necesarios, la potencia del
    campo solar y la compatibilidad con inversores disponibles.

    Incluye un cache interno para evitar llamadas repetidas a la API de PVGIS.
    """

    _PVGIS_CACHE = {}
    _PVGIS_CACHE_MAX_SIZE = 50
    
    @staticmethod
    def _get_pvgis_data_cached(lat, lon, start_year, end_year):
        """
        Obtiene datos de PVGIS con cache para evitar llamadas repetidas
        a la API con los mismos parámetros
        """
        # Crear clave única para el cache
        cache_key = f"{lat:.4f}_{lon:.4f}_{start_year}_{end_year}"
        
        # Verificar si ya está en cache
        if cache_key in AnalysisController._PVGIS_CACHE:
            logger.debug("Cache hit para: %s", cache_key)
            return AnalysisController._PVGIS_CACHE[cache_key]

        logger.debug("Cache miss, llamando a PVGIS para: %s", cache_key)

        # Limpiar cache si es muy grande (FIFO)
        if len(AnalysisController._PVGIS_CACHE) >= AnalysisController._PVGIS_CACHE_MAX_SIZE:
            # Eliminar la entrada más antigua
            oldest_key = next(iter(AnalysisController._PVGIS_CACHE))
            del AnalysisController._PVGIS_CACHE[oldest_key]
            logger.debug("Cache limpiado, eliminada entrada: %s", oldest_key)
        
        # Llamar a la API de PVGIS
        df, meta = pvlib.iotools.get_pvgis_hourly(
            latitude=lat,
            longitude=lon,
            start=start_year,
            end=end_year,
            raddatabase='PVGIS-SARAH3',
            surface_tilt=0,
            surface_azimuth=180,
            components=True,
            usehorizon=True,
            outputformat='json'
        )
        
        # Guardar en cache
        AnalysisController._PVGIS_CACHE[cache_key] = (df, meta)
        logger.debug("Datos guardados en cache. Tamaño actual: %s", len(AnalysisController._PVGIS_CACHE))
        
        return df, meta

    @staticmethod
    def calculate_panel_requirements(data):
        """Calcula los requisitos de paneles y encuentra inversores compatibles"""
        try:
            if not data or data.get('panel_id') in (None, ''):
                return jsonify({"error": "El campo 'panel_id' es requerido."}), 400

            panel = Panel.query.get(data['panel_id'])
            if not panel:
                return jsonify({"error": "Panel no encontrado"}), 400
            
            inverter_id = data.get('inverter_id')
            inverter = None
            if inverter_id:
                inverter = Inverter.query.get(inverter_id)
                if not inverter:
                    return jsonify({"error": "Inversor no encontrado"}), 400
                required_inverter_fields = {
                    'y': inverter.y, 'power': inverter.power, 'vmax': inverter.vmax,
                }
                missing_inv = [k for k, v in required_inverter_fields.items() if v is None]
                if missing_inv:
                    return jsonify({
                        "error": f"El inversor '{inverter.nombre}' tiene campos incompletos en la base de datos: {', '.join(missing_inv)}. Contacta al administrador."
                    }), 400

            required_panel_fields = {
                'tcp': panel.tcp, 't_noct': panel.t_noct, 'power': panel.power,
                'y': panel.y, 'width': panel.width, 'height': panel.height,
                'tcv': panel.tcv, 'voc': panel.voc, 'isc': panel.isc,
            }
            missing = [k for k, v in required_panel_fields.items() if v is None]
            if missing:
                return jsonify({
                    "error": f"El panel '{panel.nombre}' tiene campos incompletos en la base de datos: {', '.join(missing)}. Contacta al administrador."
                }), 400

            required_inputs = ['latitud', 'longitud', 'autoconsumo', 'necesidad']
            missing_inputs = [k for k in required_inputs if data.get(k) in (None, '')]
            if missing_inputs:
                return jsonify({
                    "error": f"Faltan campos requeridos en el cuerpo JSON: {', '.join(missing_inputs)}."
                }), 400

            try:
                lat = float(data.get('latitud'))
                lon = float(data.get('longitud'))
                autoconsumo = float(data.get('autoconsumo')) / 100
                necesidad = float(data.get('necesidad'))
            except (TypeError, ValueError):
                return jsonify({
                    "error": "Los campos 'latitud', 'longitud', 'autoconsumo' y 'necesidad' deben ser numéricos."
                }), 400

            if autoconsumo <= 0:
                return jsonify({"error": "El campo 'autoconsumo' debe ser mayor que 0."}), 400
            if necesidad <= 0:
                return jsonify({"error": "El campo 'necesidad' debe ser mayor que 0."}), 400
            if panel.width <= 0 or panel.height <= 0:
                return jsonify({
                    "error": f"El panel '{panel.nombre}' tiene dimensiones invalidas: 'width' y 'height' deben ser mayores que 0."
                }), 400

            coplanar = bool(data.get('coplanar'))
            start_year = int(data.get('start', 2020))
            end_year = int(data.get('end', 2023))

            panel_temp_loss = panel.tcp
            cell_noct = panel.t_noct
            power_placa = panel.power
            y_placa = panel.y / 100
            cell_area = (panel.width * panel.height) / 1000000
            coeficiente_v_temp = panel.tcv
            voc_cell = panel.voc

            sample_years = end_year - start_year + 1
            beta_optimal = abs(lat) * 0.69 + 3.7

            if coplanar:
                inclinacion = float(data.get('inclinacion'))
                azimut = float(data.get('azimut')) - 180
            else:
                inclinacion = beta_optimal
                azimut = 0

            # Obtener datos de irradiancia CON CACHE
            df, meta = AnalysisController._get_pvgis_data_cached(lat, lon, start_year, end_year)

            # Filtrar datos con irradiancia significativa
            filtered_df = df[df[['poa_direct', 'poa_sky_diffuse', 'poa_ground_diffuse']].sum(axis=1) > 100]

            # Calcular temperatura de celda
            filtered_df = filtered_df.copy()
            filtered_df['temp_cell'] = filtered_df['temp_air'] + (filtered_df['poa_direct'] + filtered_df['poa_sky_diffuse'] + filtered_df['poa_ground_diffuse']) * ((cell_noct - 20 ) / 800)
            
            # Temperatura promedio de celda mientras hay sol
            cell_temp = filtered_df['temp_cell'].mean()

            # Temperatura mínima del aire
            coldest_temp = filtered_df['temp_air'].min()

            # Irradiancia anual - CORREGIDO: usar sample_years correctamente
            annual_irradiance = (df['poa_direct'] + df['poa_sky_diffuse'] + df['poa_ground_diffuse']).sum() / (1000 * sample_years)  # kWh/m²

            # Factor de pérdida por irradiancia
            if (inclinacion > 15):
                irradiance_factor_loss = 1 - (1.2 * 0.0001 * (inclinacion - beta_optimal)**2 + 3.5 * 0.00001 * azimut**2)
            else:
                irradiance_factor_loss = 1 - (1.2 * 0.0001 * (inclinacion - beta_optimal)**2)
            
            # Pérdida por temperatura
            temp_power_loss = 1 - ((25 - (cell_temp + OPERATION_TEMP_CELL)/2) * panel_temp_loss / 100)

            # Determinar y_inversor
            if inverter:
                y_inversor = inverter.y / 100
            else:
                y_inversor = 0.97  # Valor por defecto

            # Eficiencia total del sistema
            total_y = y_placa * y_inversor * WIRES_LOSS * DIRTY_LOSS * temp_power_loss * irradiance_factor_loss
            
            # Energías
            sec_energy = necesidad / (autoconsumo * 1000)
            sec_net_energy = necesidad / (total_y * autoconsumo * 1000) 

            # Irradiancia óptima
            optimal_irradiance = annual_irradiance / (1 - 4.46 * 0.0001 * beta_optimal - 1.19 * 0.0001 * (beta_optimal)**2) 

            # Área de paneles necesaria
            optimal_cell_area = sec_net_energy * 1000 / optimal_irradiance

            # Cantidad de paneles
            cell_amount = optimal_cell_area / cell_area

            # Potencia total del campo
            total_field_power = math.ceil(cell_amount) * power_placa / 1000
            
            # Calcular max_cell_amount solo si hay inversor específico
            max_cell_amount = None
            if inverter:
                max_cell_amount = inverter.vmax / (
                    coeficiente_v_temp * (coldest_temp - 25) + voc_cell
                )
            
            vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

            compatible_inverters = []
            if not inverter:
                show_all_inverters = bool(data.get('show_all_inverters'))
                compatible_inverters = AnalysisController._find_compatible_inverters(
                    panel, total_field_power, coldest_temp, cell_amount, show_all_inverters
                )

            coldest_day_v_max = vmax_coldest_day * 1.05 * math.ceil(cell_amount)
            panel_protection_v = coldest_day_v_max * 1.2
            panel_protection_i = panel.isc * 1.25
            
            # Extraer altitud del meta de PVGIS
            altitude = None
            if isinstance(meta, dict):
                altitude = meta.get('inputs', {}).get('location', {}).get('elevation')

            # Produccion anual estimada: P_pico * HSP * PR
            # PR (Performance Ratio) = total_y / y_placa (panel eff ya esta en P_pico)
            performance_ratio = total_y / y_placa if y_placa > 0 else 0
            annual_production = round(total_field_power * optimal_irradiance * performance_ratio, 2)

            # Calcular desglose mensual de irradiancia y producción
            df_total_irr = (df['poa_direct'] + df['poa_sky_diffuse'] + df['poa_ground_diffuse'])
            monthly_irradiance = (df_total_irr.groupby(df_total_irr.index.month).sum() / (1000 * sample_years)).round(2).tolist()
            monthly_production = [round(val * total_field_power * performance_ratio, 2) for val in monthly_irradiance]

            # Preparar respuesta base
            response_data = {
                "total_field_power": total_field_power,
                "cache_info": f"Cache size: {len(AnalysisController._PVGIS_CACHE)}",
                "coldest_day_v_max": coldest_day_v_max,
                "altitude": altitude,
                "annual_production": annual_production,
                "monthly_irradiance": monthly_irradiance,
                "monthly_production": monthly_production,
            }

            # Agregar datos completos si hay inversor específico
            if inverter:
                response_data.update({
                    "coldest_temperature": coldest_temp,
                    "annual_irradiance_kWh_m2": round(annual_irradiance, 2),
                    "beta_optimal": beta_optimal,
                    "irradiance_factor_loss": irradiance_factor_loss,
                    "temp_power_loss": temp_power_loss,
                    "cell_temp": cell_temp,
                    "cell_area": optimal_cell_area,
                    "total_y": total_y,
                    "sec_energy": sec_energy,
                    "sec_net_energy": sec_net_energy,
                    "optimal_irradiance": optimal_irradiance,
                    "cell_amount": cell_amount,
                    "max_cell_amount": max_cell_amount,
                    "panel_protection_v": panel_protection_v,
                    "panel_protection_i": panel_protection_i,
                    "meta": meta,
                    "selected_inverter": {
                        "id": inverter.id,
                        "nombre": inverter.nombre,
                        "power": inverter.power,
                        "vmax": inverter.vmax,
                        "y": inverter.y
                    }
                })
            else:
                # Si no hay inversor específico, incluir inversores compatibles
                response_data["compatible_inverters"] = compatible_inverters
            
            return jsonify(response_data)
            
        except Exception:
            logger.exception("Error en calculate_panel_requirements")
            return jsonify({"error": "Error interno del servidor"}), 500

    @staticmethod
    def _find_compatible_inverters(panel, total_field_power, coldest_temp, cell_amount, show_all=False):
        """Encuentra inversores compatibles basado en el panel y potencia del campo"""
        try:
            vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

            if show_all:
                compatible_inverters = Inverter.query.filter(
                    (vmax_coldest_day * 1.05 * math.ceil(cell_amount)) < Inverter.vmax
                ).order_by(Inverter.power).all()
            else:
                compatible_inverters = Inverter.query.filter(
                    ((vmax_coldest_day * 1.05 * math.ceil(cell_amount) ) < Inverter.vmax) &
                    (total_field_power > Inverter.power) &
                    ((total_field_power * 0.8 ) < Inverter.power)
                ).all()

                if len(compatible_inverters) <= 1:
                    alternative_inverter = Inverter.query.filter(
                        Inverter.power >= total_field_power
                    ).order_by(
                        Inverter.power,
                    ).first()

                    if alternative_inverter:
                        compatible_inverters = [alternative_inverter]
            
            # Formatear respuesta
            inverters_data = []
            for inverter in compatible_inverters:
                inverters_data.append({
                    "id": inverter.id,
                    "nombre": inverter.nombre,
                    "power": inverter.power,
                    "vmax": inverter.vmax,
                    "y": inverter.y,
                    "I_max_input": inverter.I_max_input,
                    "I_max_output": inverter.I_max_output,
                    "vmax_coldest_day": round(vmax_coldest_day, 2),
                    "compatibility_margin": round((inverter.vmax - vmax_coldest_day) / inverter.vmax * 100, 1),
                    "power_ratio": round(total_field_power / inverter.power * 100, 1)
                })
            
            return inverters_data
            
        except Exception:
            logger.exception("Error buscando inversores compatibles")
            return []

    # Holiiii... este es mi intento por hacer algo util
    # Delta_V = 0.015
    # I_wire_input = i_mp_panel
    # Resistivity = 0.01724
    # section = Debe de taerse de la base de datos en funcion i_mp_panel

"""Controlador principal de analisis fotovoltaico."""

from flask import jsonify
import pvlib
import math
from app.models.panel import Panel
from app.models.inverter import Inverter

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
            print(f"✅ Cache hit para: {cache_key}")
            return AnalysisController._PVGIS_CACHE[cache_key]
        
        print(f"🔄 Cache miss, llamando a PVGIS para: {cache_key}")
        
        # Limpiar cache si es muy grande (FIFO)
        if len(AnalysisController._PVGIS_CACHE) >= AnalysisController._PVGIS_CACHE_MAX_SIZE:
            # Eliminar la entrada más antigua
            oldest_key = next(iter(AnalysisController._PVGIS_CACHE))
            del AnalysisController._PVGIS_CACHE[oldest_key]
            print(f"🧹 Cache limpiado, eliminada entrada: {oldest_key}")
        
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
        print(f"💾 Datos guardados en cache. Tamaño actual: {len(AnalysisController._PVGIS_CACHE)}")
        
        return df, meta
    
    @staticmethod
    def clear_pvgis_cache():
        """Limpia el cache de PVGIS (útil para testing o cuando hay problemas)"""
        AnalysisController._PVGIS_CACHE.clear()
        print("🗑️ Cache de PVGIS limpiado")
    
    @staticmethod
    def get_cache_stats():
        """Obtiene estadísticas del cache"""
        return {
            "cache_size": len(AnalysisController._PVGIS_CACHE),
            "cache_keys": list(AnalysisController._PVGIS_CACHE.keys())
        }
    
    @staticmethod
    def calculate_panel_requirements(data):
        """Calcula los requisitos de paneles y encuentra inversores compatibles"""
        try:
            # Obtener datos del panel desde la base de datos
            panel = Panel.query.get(data['panel_id'])
            if not panel:
                return jsonify({"error": "Panel no encontrado"}), 400
            
            # Verificar si se envió inversor_id
            inverter_id = data.get('inverter_id')
            inverter = None
            if inverter_id:
                inverter = Inverter.query.get(inverter_id)
                if not inverter:
                    return jsonify({"error": "Inversor no encontrado"}), 400
            
            # Parámetros fijos
            dirty_loss = 0.97
            wires_loss = 0.985
            Operation_temp_cell = 50
            
            # Obtener datos del request
            lat = float(data.get('latitud'))
            lon = float(data.get('longitud'))
            coplanar = bool(data.get('coplanar'))
            start_year = int(data.get('start', 2020))
            end_year = int(data.get('end', 2023))
            autoconsumo = float(data.get('autoconsumo')) / 100
            necesidad = float(data.get('necesidad'))
            
            # Parámetros del panel desde la base de datos
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

            if lat is None or lon is None:
                return jsonify({
                    "error": "Debes enviar 'lat' y 'lon' en el cuerpo JSON."
                }), 400
            
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
            temp_power_loss = 1 - ((25 - (cell_temp + Operation_temp_cell)/2) * panel_temp_loss / 100)

            # Determinar y_inversor
            if inverter:
                y_inversor = inverter.y / 100
            else:
                y_inversor = 0.97  # Valor por defecto

            # Eficiencia total del sistema
            total_y = y_placa * y_inversor * wires_loss * dirty_loss * temp_power_loss * irradiance_factor_loss
            
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
                    coeficiente_v_temp * (((coldest_temp + df['temp_air'].min()) / 2) - 25) + voc_cell
                )
            
            vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

            compatible_inverters = []
            if not inverter:  # Solo buscar alternativas si no se especificó un inversor
                compatible_inverters = AnalysisController._find_compatible_inverters(
                    panel, total_field_power, coldest_temp, cell_amount
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
            monthly_production = [round(val * total_field_power * performance_ratio / annual_irradiance, 2) if annual_irradiance > 0 else 0 for val in monthly_irradiance]

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
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def _find_compatible_inverters(panel, total_field_power, coldest_temp, cell_amount):
        """Encuentra inversores compatibles basado en el panel y potencia del campo"""
        try:
            # Calcular vmax_coldest_day
            vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

            # Consultar inversores que cumplan las condiciones
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
            
        except Exception as e:
            print(f"Error buscando inversores compatibles: {e}")
            return []
       
    # Holiiii... este es mi intento por hacer algo util
    # Delta_V = 0.015
    # I_wire_input = i_mp_panel
    # Resistivity = 0.01724
    # section = Debe de taerse de la base de datos en funcion i_mp_panel

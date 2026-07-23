
import math
import logging

from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.errors import ValidationError, NotFound
from app.gateways.pvgis_client import PvgisClient

logger = logging.getLogger(__name__)

DIRTY_LOSS = 0.97
WIRES_LOSS = 0.985
OPERATION_TEMP_CELL = 50

DEFAULT_ROUND_TRIP_EFFICIENCY = 0.90
DEFAULT_DOD = 0.90
DAYS_PER_YEAR = 365


class AnalysisService:

    @staticmethod
    def calculate(data, visible_catalog_ids=None):
        if not data or data.get('panel_id') in (None, ''):
            raise ValidationError("El campo 'panel_id' es requerido.")

        panel = Panel.query.get(data['panel_id'])
        if not panel or (visible_catalog_ids is not None and panel.catalog_id not in visible_catalog_ids):
            raise NotFound('Panel no encontrado')

        inverter_id = data.get('inverter_id')
        inverter = None
        if inverter_id:
            inverter = Inverter.query.get(inverter_id)
            if not inverter or (visible_catalog_ids is not None and inverter.catalog_id not in visible_catalog_ids):
                raise NotFound('Inversor no encontrado')
            required_inverter_fields = {
                'y': inverter.y, 'power': inverter.power, 'vmax': inverter.vmax,
            }
            missing_inv = [k for k, v in required_inverter_fields.items() if v is None]
            if missing_inv:
                raise ValidationError(
                    f"El inversor '{inverter.nombre}' tiene campos incompletos en la base de datos: "
                    f"{', '.join(missing_inv)}. Contacta al administrador."
                )

        required_panel_fields = {
            'tcp': panel.tcp, 't_noct': panel.t_noct, 'power': panel.power,
            'y': panel.y, 'width': panel.width, 'height': panel.height,
            'tcv': panel.tcv, 'voc': panel.voc, 'isc': panel.isc,
        }
        missing = [k for k, v in required_panel_fields.items() if v is None]
        if missing:
            raise ValidationError(
                f"El panel '{panel.nombre}' tiene campos incompletos en la base de datos: "
                f"{', '.join(missing)}. Contacta al administrador."
            )

        required_inputs = ['latitud', 'longitud', 'autoconsumo', 'necesidad']
        missing_inputs = [k for k in required_inputs if data.get(k) in (None, '')]
        if missing_inputs:
            raise ValidationError(
                f"Faltan campos requeridos en el cuerpo JSON: {', '.join(missing_inputs)}."
            )

        try:
            lat = float(data.get('latitud'))
            lon = float(data.get('longitud'))
            autoconsumo = float(data.get('autoconsumo')) / 100
            necesidad = float(data.get('necesidad'))
        except (TypeError, ValueError):
            raise ValidationError(
                "Los campos 'latitud', 'longitud', 'autoconsumo' y 'necesidad' deben ser numéricos."
            )

        if autoconsumo <= 0:
            raise ValidationError("El campo 'autoconsumo' debe ser mayor que 0.")
        if necesidad <= 0:
            raise ValidationError("El campo 'necesidad' debe ser mayor que 0.")
        if panel.width <= 0 or panel.height <= 0:
            raise ValidationError(
                f"El panel '{panel.nombre}' tiene dimensiones invalidas: "
                "'width' y 'height' deben ser mayores que 0."
            )

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

        df, meta = PvgisClient.get_hourly(lat, lon, start_year, end_year)

        filtered_df = df[df[['poa_direct', 'poa_sky_diffuse', 'poa_ground_diffuse']].sum(axis=1) > 100]

        filtered_df = filtered_df.copy()
        filtered_df['temp_cell'] = filtered_df['temp_air'] + (
            filtered_df['poa_direct'] + filtered_df['poa_sky_diffuse'] + filtered_df['poa_ground_diffuse']
        ) * ((cell_noct - 20) / 800)

        cell_temp = filtered_df['temp_cell'].mean()
        coldest_temp = filtered_df['temp_air'].min()

        annual_irradiance = (df['poa_direct'] + df['poa_sky_diffuse'] + df['poa_ground_diffuse']).sum() / (1000 * sample_years)

        if inclinacion > 15:
            irradiance_factor_loss = 1 - (1.2 * 0.0001 * (inclinacion - beta_optimal) ** 2 + 3.5 * 0.00001 * azimut ** 2)
        else:
            irradiance_factor_loss = 1 - (1.2 * 0.0001 * (inclinacion - beta_optimal) ** 2)

        temp_power_loss = 1 - ((25 - (cell_temp + OPERATION_TEMP_CELL) / 2) * panel_temp_loss / 100)

        y_inversor = inverter.y / 100 if inverter else 0.97

        total_y = y_placa * y_inversor * WIRES_LOSS * DIRTY_LOSS * temp_power_loss * irradiance_factor_loss

        sec_energy = necesidad / (autoconsumo * 1000)
        sec_net_energy = necesidad / (total_y * autoconsumo * 1000)

        optimal_irradiance = annual_irradiance / (1 - 4.46 * 0.0001 * beta_optimal - 1.19 * 0.0001 * (beta_optimal) ** 2)

        optimal_cell_area = sec_net_energy * 1000 / optimal_irradiance
        cell_amount = optimal_cell_area / cell_area
        total_field_power = math.ceil(cell_amount) * power_placa / 1000

        max_cell_amount = None
        if inverter:
            max_cell_amount = inverter.vmax / (
                coeficiente_v_temp * (coldest_temp - 25) + voc_cell
            )

        vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

        compatible_inverters = []
        if not inverter:
            show_all_inverters = bool(data.get('show_all_inverters'))
            compatible_inverters = AnalysisService._find_compatible_inverters(
                panel, total_field_power, coldest_temp, cell_amount,
                show_all_inverters, visible_catalog_ids,
            )

        coldest_day_v_max = vmax_coldest_day * 1.05 * math.ceil(cell_amount)
        panel_protection_v = coldest_day_v_max * 1.2
        panel_protection_i = panel.isc * 1.25

        altitude = None
        if isinstance(meta, dict):
            altitude = meta.get('inputs', {}).get('location', {}).get('elevation')

        performance_ratio = total_y / y_placa if y_placa > 0 else 0
        annual_production = round(total_field_power * optimal_irradiance * performance_ratio, 2)

        df_total_irr = (df['poa_direct'] + df['poa_sky_diffuse'] + df['poa_ground_diffuse'])
        monthly_irradiance = (df_total_irr.groupby(df_total_irr.index.month).sum() / (1000 * sample_years)).round(2).tolist()
        monthly_production = [round(val * total_field_power * performance_ratio, 2) for val in monthly_irradiance]

        result = {
            'total_field_power': total_field_power,
            'cache_info': f'Cache size: {PvgisClient.cache_size()}',
            'coldest_day_v_max': coldest_day_v_max,
            'altitude': altitude,
            'annual_production': annual_production,
            'monthly_irradiance': monthly_irradiance,
            'monthly_production': monthly_production,
        }

        if inverter:
            result.update({
                'coldest_temperature': coldest_temp,
                'annual_irradiance_kWh_m2': round(annual_irradiance, 2),
                'beta_optimal': beta_optimal,
                'irradiance_factor_loss': irradiance_factor_loss,
                'temp_power_loss': temp_power_loss,
                'cell_temp': cell_temp,
                'cell_area': optimal_cell_area,
                'total_y': total_y,
                'sec_energy': sec_energy,
                'sec_net_energy': sec_net_energy,
                'optimal_irradiance': optimal_irradiance,
                'cell_amount': cell_amount,
                'max_cell_amount': max_cell_amount,
                'panel_protection_v': panel_protection_v,
                'panel_protection_i': panel_protection_i,
                'meta': meta,
                'selected_inverter': {
                    'id': inverter.id,
                    'nombre': inverter.nombre,
                    'power': inverter.power,
                    'vmax': inverter.vmax,
                    'y': inverter.y,
                },
            })
        else:
            result['compatible_inverters'] = compatible_inverters

        battery_id = data.get('battery_id')
        if battery_id not in (None, ''):
            battery = Battery.query.get(battery_id)
            if not battery or (visible_catalog_ids is not None and battery.catalog_id not in visible_catalog_ids):
                raise NotFound('Bateria no encontrada')
            battery_quantity = data.get('battery_quantity') or 1
            try:
                battery_quantity = max(1, int(battery_quantity))
            except (TypeError, ValueError):
                battery_quantity = 1
            result['battery'] = AnalysisService._battery_analysis(
                battery, battery_quantity, necesidad, autoconsumo, annual_production,
            )

        return result

    @staticmethod
    def _battery_analysis(battery, quantity, necesidad, autoconsumo, annual_production):
        dod = (battery.dod / 100) if battery.dod else DEFAULT_DOD
        rte = (battery.round_trip_efficiency / 100) if battery.round_trip_efficiency else DEFAULT_ROUND_TRIP_EFFICIENCY

        if battery.usable_kwh:
            usable_per_unit = battery.usable_kwh
        elif battery.capacity_kwh and battery.dod:
            usable_per_unit = battery.capacity_kwh * dod
        else:
            usable_per_unit = battery.capacity_kwh or 0.0

        bank_usable_kwh = usable_per_unit * quantity

        daily_consumption_kwh = (necesidad / 1000) / DAYS_PER_YEAR
        daily_production_kwh = (annual_production or 0.0) / DAYS_PER_YEAR
        daily_surplus_kwh = max(0.0, daily_production_kwh - daily_consumption_kwh * autoconsumo)
        daily_unmet_kwh = daily_consumption_kwh * (1 - autoconsumo)

        deliverable_kwh = bank_usable_kwh * rte
        daily_battery_kwh = min(deliverable_kwh, daily_surplus_kwh, daily_unmet_kwh)

        uplift_pct = (daily_battery_kwh / daily_consumption_kwh * 100) if daily_consumption_kwh > 0 else 0.0
        estimated_self_consumption_pct = min(100.0, autoconsumo * 100 + uplift_pct)

        recommended_usable_kwh = daily_surplus_kwh
        recommended_capacity_kwh = (recommended_usable_kwh / dod) if dod > 0 else recommended_usable_kwh

        return {
            'battery_id': battery.id,
            'nombre': battery.nombre,
            'quantity': quantity,
            'bank_usable_kwh': round(bank_usable_kwh, 2),
            'bank_capacity_kwh': round((battery.capacity_kwh or 0.0) * quantity, 2),
            'round_trip_efficiency': round(rte, 3),
            'dod': round(dod, 3),
            'daily_consumption_kwh': round(daily_consumption_kwh, 2),
            'daily_production_kwh': round(daily_production_kwh, 2),
            'daily_surplus_kwh': round(daily_surplus_kwh, 2),
            'recommended_usable_kwh': round(recommended_usable_kwh, 2),
            'recommended_capacity_kwh': round(recommended_capacity_kwh, 2),
            'annual_battery_contribution_kwh': round(daily_battery_kwh * DAYS_PER_YEAR, 2),
            'self_consumption_uplift_pct': round(uplift_pct, 1),
            'estimated_self_consumption_pct': round(estimated_self_consumption_pct, 1),
            'method': 'daily_balance_v1',
            'method_note': (
                'Estimacion por balance diario promediado (no simulacion horaria). Asume excedente '
                'diurno representativo y consumo nocturno suficiente para descargar la bateria a '
                'diario. No modela estacionalidad ni dias nublados consecutivos. La cifra fina '
                'requiere datos horarios de consumo (futuro).'
            ),
        }

    @staticmethod
    def _find_compatible_inverters(panel, total_field_power, coldest_temp, cell_amount,
                                   show_all=False, visible_catalog_ids=None):
        try:
            vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))

            base = Inverter.query
            if visible_catalog_ids is not None:
                base = base.filter(Inverter.catalog_id.in_(visible_catalog_ids))

            if show_all:
                compatible_inverters = base.filter(
                    (vmax_coldest_day * 1.05 * math.ceil(cell_amount)) < Inverter.vmax
                ).order_by(Inverter.power).all()
            else:
                compatible_inverters = base.filter(
                    ((vmax_coldest_day * 1.05 * math.ceil(cell_amount)) < Inverter.vmax) &
                    (total_field_power > Inverter.power) &
                    ((total_field_power * 0.8) < Inverter.power)
                ).all()

                if len(compatible_inverters) <= 1:
                    alternative_inverter = base.filter(
                        Inverter.power >= total_field_power
                    ).order_by(Inverter.power).first()

                    if alternative_inverter:
                        compatible_inverters = [alternative_inverter]

            inverters_data = []
            for inverter in compatible_inverters:
                inverters_data.append({
                    'id': inverter.id,
                    'nombre': inverter.nombre,
                    'power': inverter.power,
                    'vmax': inverter.vmax,
                    'y': inverter.y,
                    'I_max_input': inverter.I_max_input,
                    'I_max_output': inverter.I_max_output,
                    'vmax_coldest_day': round(vmax_coldest_day, 2),
                    'compatibility_margin': round((inverter.vmax - vmax_coldest_day) / inverter.vmax * 100, 1),
                    'power_ratio': round(total_field_power / inverter.power * 100, 1),
                })

            return inverters_data

        except Exception:
            logger.exception('Error buscando inversores compatibles')
            return []

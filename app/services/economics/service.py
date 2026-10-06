"""Motor económico horario: perfil de consumo × producción PVGIS × tarifa.

La producción horaria se deriva de la forma de la irradiancia horaria de PVGIS
(ya cacheada 30 días, convertida a hora local Europe/Madrid) escalada por la
producción anual del análisis vigente del proyecto — así hereda las pérdidas ya
validadas sin duplicar la física; la variación horaria de pérdidas térmicas se
desprecia (asunción declarada). El aporte de la batería es la
diferencia real de factura anual entre el sistema con y sin ella (impuestos,
término de potencia y hucha incluidos): una sola cifra, la que paga el cliente.
"""

import math

from app.errors import ValidationError
from app.gateways.pvgis_client import PvgisClient
from app.models.consumption_profile import ConsumptionProfile
from app.services.consumption.expanders import HOURS_YEAR
from app.services.economics.simulator import simulate
from app.services.economics.tariff import PERIODS, annual_bill, price_of
from app.services.org_service import OrgService

PVGIS_START_YEAR = 2020
PVGIS_END_YEAR = 2023
KWP_FACTORS = (0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6)
JANUARY = (0, 31)
JULY = (181, 212)


class EconomicsService:

    @staticmethod
    def production_shape(lat, lon):
        df, _ = PvgisClient.get_hourly(lat, lon, PVGIS_START_YEAR, PVGIS_END_YEAR)
        poa = df['poa_global']
        local = poa.tz_convert('Europe/Madrid')
        grouped = local.groupby([local.index.month, local.index.day, local.index.hour]).mean()
        shape = [
            float(grouped.get((m, d, h), 0.0))
            for m, days in enumerate(
                (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31), start=1)
            for d in range(1, days + 1)
            for h in range(24)
        ]
        total = sum(shape)
        if total <= 0:
            raise ValidationError('PVGIS no devolvió irradiancia para estas coordenadas.', code='economics.no_irradiance')
        return [v / total for v in shape]

    @staticmethod
    def _series(project):
        if not project.consumption_profile_id:
            raise ValidationError('El proyecto no tiene perfil de consumo asociado.', code='economics.no_profile')
        if not project.necesidad:
            raise ValidationError('El proyecto no tiene consumo anual (necesidad).', code='economics.no_necesidad')
        resultados = project.resultados or {}
        annual_production = resultados.get('annual_production')
        if not annual_production:
            raise ValidationError('Calcula primero el dimensionamiento en el paso Análisis.', code='economics.no_analysis')
        if project.latitud is None or project.longitud is None:
            raise ValidationError('El proyecto no tiene coordenadas.', code='economics.no_coords')
        profile = ConsumptionProfile.query.get(project.consumption_profile_id)
        if profile is None or profile.is_deleted:
            raise ValidationError('El perfil de consumo del proyecto ya no existe.', code='economics.profile_gone')
        fractions = profile.fractions
        if not fractions or len(fractions) != HOURS_YEAR:
            raise ValidationError('El perfil de consumo no está materializado.', code='economics.profile_empty')
        consumption = [f * project.necesidad for f in fractions]
        shape = EconomicsService.production_shape(project.latitud, project.longitud)
        production = [s * annual_production for s in shape]
        return consumption, production

    @staticmethod
    def _battery_params(battery, quantity):
        q = max(1, int(quantity or 1))
        return {
            'capacity_kwh': battery.capacity_kwh * q,
            'power_kw': battery.power_kw * q,
            'dod': battery.dod,
            'round_trip_efficiency': battery.round_trip_efficiency,
        }

    @staticmethod
    def _day_type(series, start, end):
        hours = [0.0] * 24
        for d in range(start, end):
            for h in range(24):
                hours[h] += series[d * 24 + h]
        days = end - start
        return [round(v / days, 4) for v in hours]

    @staticmethod
    def _bill(sim, tariff, potencia_kw):
        monthly_cost = [
            sum(sim['imports'][m][p] * price_of(tariff, p) for p in PERIODS)
            for m in range(12)
        ]
        monthly_credit = [sim['exports'][m] * tariff['precio_excedente'] for m in range(12)]
        return annual_bill(tariff, monthly_cost, monthly_credit, potencia_kw)

    @classmethod
    def compute(cls, project, org_id, battery=None, quantity=1):
        consumption, production = cls._series(project)
        tariff = OrgService.get_tariff_profile(org_id)
        potencia = project.potencia_contratada or 4.6
        zeros = [0.0] * HOURS_YEAR

        base = simulate(consumption, zeros)
        fv = simulate(consumption, production)
        factura_base = cls._bill(base, tariff, potencia)
        factura_fv = cls._bill(fv, tariff, potencia)

        result = {
            'tarifa': tariff,
            'potencia_contratada_kw': potencia,
            'consumo_anual_kwh': round(fv['consumo_total'], 1),
            'produccion_anual_kwh': round(fv['produccion_total'], 1),
            'factura_base': factura_base,
            'factura_fv': factura_fv,
            'ahorro_fv': round(factura_base['total'] - factura_fv['total'], 2),
            'autoconsumo_directo_pct': round(fv['autoconsumo_directo'] / fv['consumo_total'] * 100, 1),
            'dia_tipo': {
                'invierno': {
                    'consumo': cls._day_type(consumption, *JANUARY),
                    'produccion': cls._day_type(production, *JANUARY),
                },
                'verano': {
                    'consumo': cls._day_type(consumption, *JULY),
                    'produccion': cls._day_type(production, *JULY),
                },
            },
        }

        if battery is not None:
            sim_bat = simulate(consumption, production, cls._battery_params(battery, quantity))
            factura_bat = cls._bill(sim_bat, tariff, potencia)
            result['bateria'] = {
                'id': battery.id,
                'nombre': battery.nombre,
                'cantidad': max(1, int(quantity or 1)),
                'factura': factura_bat,
                'ahorro_bateria': round(factura_fv['total'] - factura_bat['total'], 2),
                'descarga_anual_kwh': round(sim_bat['descarga_bateria'], 1),
                'autoconsumo_total_pct': round(
                    (sim_bat['autoconsumo_directo'] + sim_bat['descarga_bateria'])
                    / sim_bat['consumo_total'] * 100, 1),
            }
            result['ahorro_total'] = round(factura_base['total'] - factura_bat['total'], 2)
        else:
            result['ahorro_total'] = result['ahorro_fv']

        return result

    @classmethod
    def scenarios(cls, project, org_id, batteries):
        consumption, production = cls._series(project)
        tariff = OrgService.get_tariff_profile(org_id)
        potencia = project.potencia_contratada or 4.6

        base = simulate(consumption, [0.0] * HOURS_YEAR)
        factura_base = cls._bill(base, tariff, potencia)['total']
        fv = simulate(consumption, production)
        factura_fv = cls._bill(fv, tariff, potencia)['total']

        rows = [{
            'battery_id': None,
            'nombre': 'Sin batería',
            'capacity_kwh': 0.0,
            'factura_anual': round(factura_fv, 2),
            'ahorro_anual': round(factura_base - factura_fv, 2),
            'ahorro_bateria': 0.0,
            'precio_bateria': None,
            'payback_bateria_anios': None,
        }]
        for battery in batteries:
            sim = simulate(consumption, production, cls._battery_params(battery, 1))
            factura = cls._bill(sim, tariff, potencia)['total']
            valor = factura_fv - factura
            payback = None
            if battery.precio_unitario and valor > 0:
                payback = round(battery.precio_unitario / valor, 1)
            rows.append({
                'battery_id': battery.id,
                'nombre': battery.nombre,
                'capacity_kwh': battery.capacity_kwh,
                'factura_anual': round(factura, 2),
                'ahorro_anual': round(factura_base - factura, 2),
                'ahorro_bateria': round(valor, 2),
                'precio_bateria': battery.precio_unitario,
                'payback_bateria_anios': payback,
            })
        rows.sort(key=lambda r: -r['ahorro_anual'])
        return {'factura_base': round(factura_base, 2), 'escenarios': rows}

    @staticmethod
    def _system_cost(kwp, panel, inverter, battery, budget):
        if panel is None or not panel.precio_unitario or not panel.power:
            return None
        if battery is not None and not battery.precio_unitario:
            return None
        n_panels = math.ceil(kwp * 1000.0 / panel.power)
        cost = n_panels * panel.precio_unitario
        cost += budget.get('labor_fixed') or 0.0
        cost += (budget.get('labor_per_panel') or 0.0) * n_panels
        if inverter is not None and inverter.precio_unitario:
            cost += inverter.precio_unitario
        if battery is not None:
            cost += battery.precio_unitario
        return round(cost, 2)

    @classmethod
    def sweep(cls, project, org_id, batteries):
        consumption, production = cls._series(project)
        tariff = OrgService.get_tariff_profile(org_id)
        budget = OrgService.get_budget_profile(org_id)
        potencia = project.potencia_contratada or 4.6
        base_kwp = (project.resultados or {}).get('total_field_power')
        if not base_kwp:
            raise ValidationError('El análisis guardado no tiene potencia de campo.', code='economics.no_field_power')

        factura_base = cls._bill(simulate(consumption, [0.0] * HOURS_YEAR), tariff, potencia)['total']
        kwp_points = [round(base_kwp * f, 2) for f in KWP_FACTORS]

        pool = sorted(batteries, key=lambda b: (b.id != project.battery_id, not b.precio_unitario, b.capacity_kwh))
        candidates = [None] + pool[:3]

        series = []
        sin_precio = []
        for battery in candidates[:4]:
            params = cls._battery_params(battery, 1) if battery else None
            ahorros = []
            costes = []
            for f in KWP_FACTORS:
                scaled = [v * f for v in production]
                sim = simulate(consumption, scaled, params)
                factura = cls._bill(sim, tariff, potencia)['total']
                ahorros.append(round(factura_base - factura, 2))
                costes.append(cls._system_cost(base_kwp * f, project.panel, project.inverter, battery, budget))
            complete = all(c is not None for c in costes)
            if not complete and battery is not None:
                sin_precio.append(battery.nombre)
            series.append({
                'battery_id': battery.id if battery else None,
                'nombre': battery.nombre if battery else 'Sin batería',
                'capacity_kwh': battery.capacity_kwh if battery else 0.0,
                'ahorros': ahorros,
                'costes': costes if complete else None,
            })

        return {
            'kwp': kwp_points,
            'techo': round(factura_base, 2),
            'series': series,
            'sin_precio': sin_precio,
        }

"""Motor económico horario: perfil de consumo × producción PVGIS × tarifa.

La producción horaria se deriva de la forma de la irradiancia horaria de PVGIS
(ya cacheada 30 días, convertida a hora local Europe/Madrid) escalada por la
producción anual del análisis vigente del proyecto — así hereda las pérdidas ya
validadas sin duplicar la física; la variación horaria de pérdidas térmicas se
desprecia (asunción declarada). El aporte de la batería se valora como
descarga × (precio del periodo − precio de excedente): el contrafactual de esa
energía era venderse como excedente.
"""

from app.errors import ValidationError
from app.gateways.pvgis_client import PvgisClient
from app.models.consumption_profile import ConsumptionProfile
from app.services.consumption.expanders import HOURS_YEAR
from app.services.economics.simulator import simulate
from app.services.economics.tariff import PERIODS, annual_bill, price_of
from app.services.org_service import OrgService

PVGIS_START_YEAR = 2020
PVGIS_END_YEAR = 2023


class EconomicsService:

    @staticmethod
    def production_shape(lat, lon):
        df, _ = PvgisClient.get_hourly(lat, lon, PVGIS_START_YEAR, PVGIS_END_YEAR)
        poa = (df['poa_direct'] + df['poa_sky_diffuse'] + df['poa_ground_diffuse'])
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
    def _bill(sim, tariff, potencia_kw):
        monthly_cost = [
            sum(sim['imports'][m][p] * price_of(tariff, p) for p in PERIODS)
            for m in range(12)
        ]
        monthly_credit = [sim['exports'][m] * tariff['precio_excedente'] for m in range(12)]
        return annual_bill(tariff, monthly_cost, monthly_credit, potencia_kw)

    @staticmethod
    def _battery_value(sim, tariff):
        return sum(
            sim['discharge'][m][p] * max(0.0, price_of(tariff, p) - tariff['precio_excedente'])
            for m in range(12) for p in PERIODS
        )

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
        }

        if battery is not None:
            sim_bat = simulate(consumption, production, cls._battery_params(battery, quantity))
            factura_bat = cls._bill(sim_bat, tariff, potencia)
            result['bateria'] = {
                'id': battery.id,
                'nombre': battery.nombre,
                'cantidad': max(1, int(quantity or 1)),
                'factura': factura_bat,
                'ahorro_bateria': round(cls._battery_value(sim_bat, tariff), 2),
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
            valor = cls._battery_value(sim, tariff)
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

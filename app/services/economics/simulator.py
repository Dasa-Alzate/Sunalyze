"""Balance energético horario con batería sobre las 8760 horas canónicas.

Puerto del simulador del asesor con los arreglos acordados: calendario canónico
(fin de semana real por convención), determinismo absoluto, y límite de potencia
de carga/descarga de la batería (power_kw del catálogo) que el original ignoraba.
La eficiencia de ida y vuelta se reparte a partes iguales entre carga y descarga.
"""

import math

import pandas as pd

from app.services.consumption.expanders import DAYS_PER_MONTH, HOURS_YEAR
from app.services.economics.tariff import PERIODS, period_of

_MONTH_OF_DAY = [m for m, days in enumerate(DAYS_PER_MONTH) for _ in range(days)]


def simulate(consumption, production, battery=None):
    """Recorre el año hora a hora y agrega importación por mes y periodo.

    battery: {'capacity_kwh', 'power_kw', 'dod', 'round_trip_efficiency'} o None.
    Devuelve agregados mensuales y anuales en kWh, con la descarga de batería
    desglosada por periodo tarifario para poder valorarla económicamente.
    """
    if len(consumption) != HOURS_YEAR or len(production) != HOURS_YEAR:
        raise ValueError(f'las series deben tener {HOURS_YEAR} horas')

    cap = battery['capacity_kwh'] if battery else 0.0
    power = battery['power_kw'] if battery else 0.0
    dod = (battery.get('dod') or 90.0) / 100.0 if battery else 0.0
    rte = (battery.get('round_trip_efficiency') or 90.0) / 100.0 if battery else 1.0
    ef = math.sqrt(rte)
    soc_min = cap * (1.0 - dod)
    soc = max(soc_min, cap * 0.5) if battery else 0.0

    imports = [{p: 0.0 for p in PERIODS} for _ in range(12)]
    discharge = [{p: 0.0 for p in PERIODS} for _ in range(12)]
    exports = [0.0] * 12
    direct_by_month = [0.0] * 12
    charge_by_month = [0.0] * 12
    direct = 0.0
    charged = 0.0
    hourly_rows = []

    for h in range(HOURS_YEAR):
        day = h // 24 + 1
        month = _MONTH_OF_DAY[day - 1]
        hour = h % 24
        period = period_of(day, hour)
        cons = consumption[h]
        prod = production[h]

        auto = min(cons, prod)
        direct += auto
        direct_by_month[month] += auto
        surplus = prod - auto
        deficit = cons - auto
        charge = 0.0
        out = 0.0

        if cap > 0.0 and surplus > 0.0:
            room = (cap - soc) / ef
            charge = min(surplus, power, room)
            soc += charge * ef
            charged += charge
            charge_by_month[month] += charge
            surplus -= charge
        elif cap > 0.0 and deficit > 0.0:
            available = (soc - soc_min) * ef
            out = min(deficit, power, available)
            soc -= out / ef
            discharge[month][period] += out
            deficit -= out

        exports[month] += surplus
        imports[month][period] += deficit
        hourly_rows.append((
            h, month + 1, day, hour, cons, prod, auto, charge, out,
            max(0.0, surplus), max(0.0, deficit), soc,
        ))

    hourly = pd.DataFrame(hourly_rows, columns=(
        'hour_index', 'month', 'day', 'hour', 'consumption_kwh', 'production_kwh',
        'direct_self_consumption_kwh', 'battery_charge_kwh', 'battery_discharge_kwh',
        'grid_export_kwh', 'grid_import_kwh', 'soc_kwh',
    ))
    hourly.insert(0, 'timestamp', pd.date_range('2018-01-01', periods=HOURS_YEAR, freq='h'))

    return {
        'hourly': hourly,
        'imports': imports,
        'discharge': discharge,
        'exports': exports,
        'autoconsumo_directo_mensual': direct_by_month,
        'carga_bateria_mensual': charge_by_month,
        'autoconsumo_directo': direct,
        'carga_bateria': charged,
        'descarga_bateria': sum(d[p] for d in discharge for p in PERIODS),
        'importacion_total': sum(i[p] for i in imports for p in PERIODS),
        'exportacion_total': sum(exports),
        'consumo_total': sum(consumption),
        'produccion_total': sum(production),
    }

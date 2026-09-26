"""Expansión de un ProfileSource a la serie canónica de 8760 fracciones horarias.

Convenciones (docs/perfil-consumo-cdm-sintesis.md): calendario canónico del
año 2018 (no bisiesto, empieza en lunes), tipos de día laborable/sabado/domingo,
anclas estacionales invierno=día 15 y verano=día 196. Cada celda de la matriz
intermedia lleva la forma intradía (24 fracciones) y el peso diario relativo, de modo
que una muestra medida conserva tanto el perfil horario como el nivel estacional.
Todo es determinista; el resultado siempre suma 1.0.
"""

import math

CDM_VERSION = 1
HOURS_YEAR = 8760
DAYS_YEAR = 365
DAY_TYPES = ('laborable', 'sabado', 'domingo')
SEASONS = ('invierno', 'verano')
WINTER_ANCHOR_DAY = 15
DAYS_PER_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class ProfilePayloadError(ValueError):
    """El payload de un ProfileSource no cumple el contrato de su kind."""


def day_type_of(day_of_year):
    """Tipo de día bajo el calendario canónico (día 1 = lunes)."""
    weekday = (day_of_year - 1) % 7
    if weekday == 5:
        return 'sabado'
    if weekday == 6:
        return 'domingo'
    return 'laborable'


def day_of_year(month, day):
    return sum(DAYS_PER_MONTH[:month - 1]) + day


def _hours_vector(raw, context):
    if not isinstance(raw, (list, tuple)) or len(raw) != 24:
        raise ProfilePayloadError(f'{context}: se esperan 24 valores horarios')
    values = []
    for v in raw:
        if not isinstance(v, (int, float)) or v < 0:
            raise ProfilePayloadError(f'{context}: valores numéricos no negativos')
        values.append(float(v))
    return values


def _cell(hours, context):
    total = sum(hours)
    if total <= 0:
        raise ProfilePayloadError(f'{context}: el día no tiene consumo')
    return {'forma': [h / total for h in hours], 'peso': total}


def _complete_day_types(cells, context):
    if not cells:
        raise ProfilePayloadError(f'{context}: sin ningún tipo de día')
    base = cells.get('laborable') or cells.get('sabado') or cells.get('domingo')
    return {dt: cells.get(dt, base) for dt in DAY_TYPES}


def _reduce_day(payload, context):
    cell = _cell(_hours_vector(payload.get('hours'), context), context)
    return {dt: cell for dt in DAY_TYPES}


def _reduce_daytypes(payload, context):
    cells = {}
    for dt in DAY_TYPES:
        if payload.get(dt) is not None:
            cells[dt] = _cell(_hours_vector(payload[dt], f'{context}.{dt}'), context)
    return _complete_day_types(cells, context)


def _reduce_week(payload, context):
    days = payload.get('days')
    if not isinstance(days, (list, tuple)) or len(days) != 7:
        raise ProfilePayloadError(f'{context}: una semana son 7 días (lunes primero)')
    vectors = [_hours_vector(d, f'{context}.dia{i + 1}') for i, d in enumerate(days)]
    laborables = [sum(vectors[i][h] for i in range(5)) / 5 for h in range(24)]
    return _complete_day_types({
        'laborable': _cell(laborables, context),
        'sabado': _cell(vectors[5], context),
        'domingo': _cell(vectors[6], context),
    }, context)


def _reduce_month(payload, context):
    month = payload.get('month')
    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ProfilePayloadError(f'{context}: month debe ser 1..12')
    days = payload.get('days')
    expected = DAYS_PER_MONTH[month - 1]
    if not isinstance(days, (list, tuple)) or len(days) != expected:
        raise ProfilePayloadError(f'{context}: el mes {month} tiene {expected} días')
    grouped = {dt: [] for dt in DAY_TYPES}
    for i, d in enumerate(days):
        dt = day_type_of(day_of_year(month, i + 1))
        grouped[dt].append(_hours_vector(d, f'{context}.dia{i + 1}'))
    cells = {}
    for dt, vectors in grouped.items():
        if vectors:
            mean = [sum(v[h] for v in vectors) / len(vectors) for h in range(24)]
            cells[dt] = _cell(mean, context)
    return _complete_day_types(cells, context)


_SAMPLE_REDUCERS = {
    'day': _reduce_day,
    'daytypes': _reduce_daytypes,
    'week': _reduce_week,
    'month': _reduce_month,
}


def _reduce_seasonal(payload):
    matrix = {}
    for season in SEASONS:
        sample = payload.get(season)
        if not isinstance(sample, dict):
            raise ProfilePayloadError(f'seasonal: falta la muestra de {season}')
        kind = sample.get('kind')
        reducer = _SAMPLE_REDUCERS.get(kind)
        if reducer is None:
            raise ProfilePayloadError(f'seasonal.{season}: kind «{kind}» no admitido dentro de seasonal')
        matrix[season] = reducer(sample, season)
    return matrix


def _summer_weight(day):
    return 0.5 * (1.0 - math.cos(2.0 * math.pi * (day - WINTER_ANCHOR_DAY) / DAYS_YEAR))


def _expand_matrix(matrix):
    seasonal = 'invierno' in matrix and 'verano' in matrix
    single = None if seasonal else next(iter(matrix.values()))
    serie = []
    for day in range(1, DAYS_YEAR + 1):
        dt = day_type_of(day)
        if seasonal:
            w = _summer_weight(day)
            inv, ver = matrix['invierno'][dt], matrix['verano'][dt]
            forma = [(1.0 - w) * inv['forma'][h] + w * ver['forma'][h] for h in range(24)]
            peso = (1.0 - w) * inv['peso'] + w * ver['peso']
        else:
            forma, peso = single[dt]['forma'], single[dt]['peso']
        serie.extend(peso * f for f in forma)
    total = sum(serie)
    return [v / total for v in serie]


def _build_annual(payload):
    values = payload.get('values')
    if not isinstance(values, (list, tuple)) or len(values) != HOURS_YEAR:
        raise ProfilePayloadError(f'annual: se esperan {HOURS_YEAR} valores horarios')
    clean = []
    for v in values:
        if not isinstance(v, (int, float)) or v < 0:
            raise ProfilePayloadError('annual: valores numéricos no negativos')
        clean.append(float(v))
    total = sum(clean)
    if total <= 0:
        raise ProfilePayloadError('annual: la serie no tiene consumo')
    hint = total if payload.get('unit', 'kwh') == 'kwh' else None
    return [v / total for v in clean], hint


def build_fractions(kind, payload):
    """Devuelve (fracciones_8760, annual_kwh_hint) para cualquier kind del CDM."""
    if not isinstance(payload, dict):
        raise ProfilePayloadError('el payload debe ser un objeto')
    if kind == 'annual':
        return _build_annual(payload)
    if kind == 'seasonal':
        return _expand_matrix(_reduce_seasonal(payload)), None
    reducer = _SAMPLE_REDUCERS.get(kind)
    if reducer is None:
        raise ProfilePayloadError(f'kind «{kind}» desconocido (admite: annual, day, daytypes, week, month, seasonal)')
    return _expand_matrix({None: reducer(payload, kind)}), None

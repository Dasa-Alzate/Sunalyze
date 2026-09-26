"""Adapters de import de perfiles de consumo: fichero → ProfileSource.

Soporta el CSV de curva horaria o cuartohoraria de las distribuidoras españolas
(Datadis / e-distribución: separador ;, decimal con coma, hora hour-ending 1..25)
y JSON (lista de 8760 valores, o los registros del cuaderno del asesor con
consumo_kwh). Normaliza cambios de hora DST, descarta el 29 de febrero y alinea
los días de la semana rotando la serie al calendario canónico (día 1 = lunes).
"""

import csv
import io
import json
import re
from datetime import date

from app.services.consumption.expanders import DAYS_PER_MONTH, DAYS_YEAR, HOURS_YEAR

_DATE_PATTERNS = (
    (re.compile(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$'), (1, 2, 3)),
    (re.compile(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$'), (3, 2, 1)),
)
_HEADER_DATE = re.compile(r'fecha|date', re.IGNORECASE)
_HEADER_HOUR = re.compile(r'hora|period|time', re.IGNORECASE)
_HEADER_VALUE = re.compile(r'consumo|consumption|kwh|valor|energ', re.IGNORECASE)


class ProfileImportError(ValueError):
    """El fichero no se pudo interpretar como perfil de consumo."""


def _parse_date(token):
    token = token.strip().split(' ')[0]
    for pattern, order in _DATE_PATTERNS:
        m = pattern.match(token)
        if m:
            y, mo, d = (int(m.group(order[0])), int(m.group(order[1])), int(m.group(order[2])))
            try:
                return date(y, mo, d)
            except ValueError:
                return None
    return None


def _parse_value(token):
    token = token.strip().replace('.', '') if token.count(',') == 1 and token.count('.') > 1 else token.strip()
    token = token.replace(',', '.')
    try:
        value = float(token)
    except ValueError:
        return None
    return value if value >= 0 else None


def _hour_index(token, quarter_counts):
    token = token.strip()
    if ':' in token:
        hh = token.split(':')[0]
        if hh.isdigit() and 0 <= int(hh) <= 23:
            quarter_counts.append(1)
            return int(hh)
        return None
    if token.isdigit():
        n = int(token)
        if 1 <= n <= 25:
            return n - 1
        if 26 <= n <= 100:
            quarter_counts.append(1)
            return min(23, (n - 1) // 4)
    return None


def _detect_columns(rows):
    for i, row in enumerate(rows[:10]):
        cols = {}
        for j, tokenraw in enumerate(row):
            token = tokenraw.strip()
            if 'date' not in cols and _HEADER_DATE.search(token):
                cols['date'] = j
            elif 'hour' not in cols and _HEADER_HOUR.search(token):
                cols['hour'] = j
            elif 'value' not in cols and _HEADER_VALUE.search(token):
                cols['value'] = j
        if len(cols) == 3:
            return i + 1, cols
    raise ProfileImportError('no encuentro cabecera con columnas de fecha, hora y consumo')


def _normalize_day(hours):
    present = [h for h in hours if h is not None]
    if len(present) < 20:
        return None
    mean = sum(present) / len(present)
    return [h if h is not None else mean for h in hours]


def _parse_csv(text):
    delimiter = ';' if text.count(';') >= text.count(',') else ','
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in r)]
    if not rows:
        raise ProfileImportError('el fichero está vacío')
    start, cols = _detect_columns(rows)
    needed = max(cols.values()) + 1
    days = {}
    quarter_counts = []
    for row in rows[start:]:
        if len(row) < needed:
            continue
        day = _parse_date(row[cols['date']])
        idx = _hour_index(row[cols['hour']], quarter_counts)
        value = _parse_value(row[cols['value']])
        if day is None or idx is None or value is None:
            continue
        if day.month == 2 and day.day == 29:
            continue
        bucket = days.setdefault(day, [None] * 24)
        slot = min(idx, 23)
        bucket[slot] = value if bucket[slot] is None else bucket[slot] + value
    clean = {}
    for day, hours in days.items():
        normalized = _normalize_day(hours)
        if normalized is not None:
            clean[day] = normalized
    if not clean:
        raise ProfileImportError('ninguna fila del fichero se pudo interpretar')
    return clean


def _month_payload(days_map):
    sample = next(iter(days_map))
    month = sample.month
    expected = DAYS_PER_MONTH[month - 1]
    by_day = {d.day: v for d, v in days_map.items()}
    if len(by_day) < expected:
        missing = sorted(set(range(1, expected + 1)) - set(by_day))
        raise ProfileImportError(f'el mes {month} está incompleto (faltan los días {missing[:5]}…)' if len(missing) > 5
                                 else f'el mes {month} está incompleto (faltan los días {missing})')
    return {'month': month, 'days': [by_day[d] for d in range(1, expected + 1)]}


def _annual_payload(days_map):
    ordered = sorted(days_map)
    mean_day = [sum(days_map[d][h] for d in ordered) / len(ordered) for h in range(24)]
    series_days = []
    cursor = ordered[0]
    for _ in range(DAYS_YEAR):
        series_days.append(days_map.get(cursor, mean_day))
        cursor = date.fromordinal(cursor.toordinal() + 1)
        if cursor.month == 2 and cursor.day == 29:
            cursor = date.fromordinal(cursor.toordinal() + 1)
    shift = ordered[0].weekday()
    rotated = series_days[shift:] + series_days[:shift]
    values = [v for day in rotated for v in day]
    return {'values': values, 'unit': 'kwh'}


def _from_days_map(days_map):
    if len(days_map) >= 360:
        return 'annual', _annual_payload(days_map)
    months = {(d.year, d.month) for d in days_map}
    if len(months) == 1:
        return 'month', _month_payload(days_map)
    raise ProfileImportError(
        f'la muestra tiene {len(days_map)} días repartidos en {len(months)} meses: '
        'se admite un año (≥360 días) o un mes natural completo'
    )


def _parse_json(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise ProfileImportError(f'JSON inválido: {err.msg}') from err
    if isinstance(data, list) and len(data) == HOURS_YEAR and all(isinstance(v, (int, float)) for v in data):
        return 'annual', {'values': [float(v) for v in data], 'unit': 'kwh'}
    if isinstance(data, list) and data and isinstance(data[0], dict) and 'consumo_kwh' in data[0]:
        if len(data) != HOURS_YEAR:
            raise ProfileImportError(f'el JSON del cuaderno debe traer {HOURS_YEAR} registros (trae {len(data)})')
        key = 'hora_global' if 'hora_global' in data[0] else None
        ordered = sorted(data, key=lambda r: r[key]) if key else sorted(
            data, key=lambda r: (r['mes'], r['dia'], r['hora']))
        return 'annual', {'values': [max(0.0, float(r['consumo_kwh'])) for r in ordered], 'unit': 'kwh'}
    raise ProfileImportError('JSON no reconocido: se admite una lista de 8760 valores o los registros del cuaderno')


def parse_consumption_file(filename, text):
    """Devuelve (kind, payload) canónicos a partir del contenido de un fichero."""
    name = (filename or '').lower()
    stripped = text.lstrip()
    if name.endswith('.json') or stripped.startswith('[') or stripped.startswith('{'):
        return _parse_json(text)
    return _from_days_map(_parse_csv(text))

"""Registry de filtros de formato del pipeline `valor | filtro(args)`.

Los filtros numéricos formatean según el *locale* de presentación (el de la jurisdicción de la
plantilla), no un es-ES fijo. El locale y la moneda llegan al filtro como `presentation` desde
el resolver, no como argumentos de la plantilla. Solo se invocan funciones registradas aquí; un
nombre no registrado produce TemplateError, nunca una llamada arbitraria. Formateo solo con
stdlib (sin babel).
"""

import math
from datetime import date, datetime

from .errors import TemplateError
from .jurisdiction import CURRENCY_SYMBOLS, CURRENCY_SYMBOL_AFTER

_LOCALE_SEPARATORS = {
    'es': (',', '.'),
    'fr': (',', ' '),
    'de': (',', '.'),
    'it': (',', '.'),
    'pt': (',', '.'),
    'en': ('.', ','),
}

_DEFAULT_SEPARATORS = (',', '.')


def _separators(locale):
    if not locale:
        return _DEFAULT_SEPARATORS
    return _LOCALE_SEPARATORS.get(locale.split('-')[0].split('_')[0].lower(), _DEFAULT_SEPARATORS)


def _is_empty(value):
    """True para valores ausentes: None o cadena en blanco (una entidad opcional sin dato)."""
    return value is None or (isinstance(value, str) and value.strip() == '')


def _coerce_number(value):
    if isinstance(value, bool):
        raise TemplateError('Se esperaba un número.')
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.replace(',', '.'))
        except ValueError:
            raise TemplateError(f"Valor no numérico: '{value}'.")
    else:
        raise TemplateError('Se esperaba un número.')
    if not math.isfinite(number):
        raise TemplateError('Valor numérico no finito.')
    return number


def _format_plain(number, decimals, decimal_sep):
    formatted = f'{number:.{decimals}f}'
    return formatted.replace('.', decimal_sep)


def _format_grouped(number, decimals, decimal_sep, thousands_sep):
    sign = '-' if number < 0 else ''
    number = abs(number)
    whole = int(number)
    grouped = f'{whole:,}'.replace(',', thousands_sep)
    if decimals > 0:
        frac = f'{number - whole:.{decimals}f}'[2:]
        return f'{sign}{grouped}{decimal_sep}{frac}'
    return f'{sign}{grouped}'


def filter_number(value, decimals=2, presentation=None):
    """Formatea con N decimales y la coma decimal del locale (sin separador de miles).

    None-safe: un valor ausente (None o cadena en blanco) devuelve '' en vez de romper, igual
    que el resto de filtros; así una entidad opcional sin dato no ensucia el documento.
    """
    if _is_empty(value):
        return ''
    decimal_sep, _ = _separators((presentation or {}).get('locale'))
    return _format_plain(_coerce_number(value), int(decimals), decimal_sep)


def filter_thousands(value, decimals=2, presentation=None):
    """Formatea con separador de miles y decimal del locale. None-safe (ausente -> '')."""
    if _is_empty(value):
        return ''
    decimal_sep, thousands_sep = _separators((presentation or {}).get('locale'))
    return _format_grouped(_coerce_number(value), int(decimals), decimal_sep, thousands_sep)


def filter_money(value, decimals=2, presentation=None):
    """Formatea un importe según la moneda y el locale de la plantilla. None-safe (ausente -> '')."""
    if _is_empty(value):
        return ''
    presentation = presentation or {}
    currency = (presentation.get('currency') or 'EUR').upper()
    decimal_sep, thousands_sep = _separators(presentation.get('locale'))
    amount = _format_grouped(_coerce_number(value), int(decimals), decimal_sep, thousands_sep)
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in CURRENCY_SYMBOL_AFTER:
        return f'{amount} {symbol}'
    return f'{symbol}{amount}'


def filter_currency(value, decimals=2, presentation=None):
    """Alias de `money`."""
    return filter_money(value, decimals, presentation=presentation)


def filter_date(value, fmt=None, presentation=None):
    """Formatea una fecha según el orden del locale (en: m/d/Y, resto: d/m/Y)."""
    if value is None or value == '':
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        raise TemplateError('Se esperaba una fecha.')
    if fmt:
        return value.strftime(fmt)
    locale = ((presentation or {}).get('locale') or '').split('-')[0].split('_')[0].lower()
    if locale == 'en':
        return value.strftime('%m/%d/%Y')
    return value.strftime('%d/%m/%Y')


def filter_ellipsis(value, max_length, presentation=None):
    """Corta el texto a `max_length` caracteres y añade … si se truncó."""
    text = '' if value is None else str(value)
    max_length = int(max_length)
    if max_length < 0:
        raise TemplateError('ellipsis requiere una longitud no negativa.')
    if len(text) <= max_length:
        return text
    return text[:max_length] + '…'


def filter_upper(value, presentation=None):
    return ('' if value is None else str(value)).upper()


def filter_lower(value, presentation=None):
    return ('' if value is None else str(value)).lower()


def filter_capitalize(value, presentation=None):
    """Primera letra en mayúscula, el resto sin tocar (no baja el resto, a diferencia de str)."""
    text = '' if value is None else str(value)
    return text[:1].upper() + text[1:] if text else ''


def filter_title(value, presentation=None):
    """Cada palabra con inicial mayúscula (útil para nombres propios en minúscula)."""
    return ('' if value is None else str(value)).title()


def filter_default(value, fallback='', presentation=None):
    """Devuelve `fallback` cuando el valor está ausente (None o cadena en blanco).

    Pareja natural de los filtros None-safe: `{{ finance.net_capex | money | default('N/D') }}`
    muestra un texto de reemplazo en vez de un hueco cuando el dato no existe.
    """
    if value is None or (isinstance(value, str) and value.strip() == ''):
        return fallback
    return value


FILTERS = {
    'number': filter_number,
    'thousands': filter_thousands,
    'money': filter_money,
    'currency': filter_currency,
    'date': filter_date,
    'ellipsis': filter_ellipsis,
    'upper': filter_upper,
    'lower': filter_lower,
    'capitalize': filter_capitalize,
    'title': filter_title,
    'default': filter_default,
}


def apply_filter(name, value, args, presentation=None):
    fn = FILTERS.get(name)
    if fn is None:
        raise TemplateError(f"Filtro desconocido: '{name}'.")
    try:
        return fn(value, *args, presentation=presentation)
    except TemplateError:
        raise
    except (TypeError, ValueError):
        raise TemplateError(f"Argumentos inválidos para el filtro '{name}'.")

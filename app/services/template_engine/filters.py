"""Registry de filtros de formato del pipeline `valor | filtro(args)`.

Los filtros numéricos formatean según el *locale* de presentación (el de la jurisdicción de la
plantilla), no un es-ES fijo. El locale y la moneda llegan al filtro como `presentation` desde
el resolver, no como argumentos de la plantilla. Solo se invocan funciones registradas aquí; un
nombre no registrado produce TemplateError, nunca una llamada arbitraria. Formateo solo con
stdlib (sin babel).
"""

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


def _coerce_number(value):
    if isinstance(value, bool):
        raise TemplateError('Se esperaba un número.')
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            raise TemplateError(f"Valor no numérico: '{value}'.")
    raise TemplateError('Se esperaba un número.')


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
    """Formatea con N decimales y la coma decimal del locale (sin separador de miles)."""
    decimal_sep, _ = _separators((presentation or {}).get('locale'))
    return _format_plain(_coerce_number(value), int(decimals), decimal_sep)


def filter_thousands(value, decimals=2, presentation=None):
    """Formatea con separador de miles y decimal del locale."""
    decimal_sep, thousands_sep = _separators((presentation or {}).get('locale'))
    return _format_grouped(_coerce_number(value), int(decimals), decimal_sep, thousands_sep)


def filter_money(value, decimals=2, presentation=None):
    """Formatea un importe según la moneda y el locale de la plantilla."""
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


FILTERS = {
    'number': filter_number,
    'thousands': filter_thousands,
    'money': filter_money,
    'currency': filter_currency,
    'date': filter_date,
    'ellipsis': filter_ellipsis,
    'upper': filter_upper,
    'lower': filter_lower,
}


def apply_filter(name, value, args, presentation=None):
    fn = FILTERS.get(name)
    if fn is None:
        raise TemplateError(f"Filtro desconocido: '{name}'.")
    try:
        return fn(value, *args, presentation=presentation)
    except TypeError:
        raise TemplateError(f"Argumentos inválidos para el filtro '{name}'.")

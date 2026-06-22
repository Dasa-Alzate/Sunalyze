"""Registry de filtros de formato del pipeline `valor | filtro(args)`.

Coherente con `frontend/src/shared/format.js`: coma decimal y punto de miles (es-ES). Solo
se invocan funciones registradas aquí; un nombre no registrado produce TemplateError, nunca
una llamada arbitraria.
"""

from .errors import TemplateError


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


def _format_decimal(number, decimals):
    formatted = f'{number:.{decimals}f}'
    return formatted.replace('.', ',')


def filter_number(value, decimals=2):
    """Formatea con N decimales y coma decimal (sin separador de miles)."""
    return _format_decimal(_coerce_number(value), int(decimals))


def filter_thousands(value, decimals=2):
    """Formatea con separador de miles (.) y coma decimal, estilo es-ES."""
    number = _coerce_number(value)
    decimals = int(decimals)
    sign = '-' if number < 0 else ''
    number = abs(number)
    whole = int(number)
    grouped = f'{whole:,}'.replace(',', '.')
    if decimals > 0:
        frac = f'{number - whole:.{decimals}f}'[2:]
        return f'{sign}{grouped},{frac}'
    return f'{sign}{grouped}'


def filter_ellipsis(value, max_length):
    """Corta el texto a `max_length` caracteres y añade … si se truncó."""
    text = '' if value is None else str(value)
    max_length = int(max_length)
    if max_length < 0:
        raise TemplateError('ellipsis requiere una longitud no negativa.')
    if len(text) <= max_length:
        return text
    return text[:max_length] + '…'


def filter_upper(value):
    return ('' if value is None else str(value)).upper()


def filter_lower(value):
    return ('' if value is None else str(value)).lower()


FILTERS = {
    'number': filter_number,
    'thousands': filter_thousands,
    'ellipsis': filter_ellipsis,
    'upper': filter_upper,
    'lower': filter_lower,
}


def apply_filter(name, value, args):
    fn = FILTERS.get(name)
    if fn is None:
        raise TemplateError(f"Filtro desconocido: '{name}'.")
    try:
        return fn(value, *args)
    except TypeError:
        raise TemplateError(f"Argumentos inválidos para el filtro '{name}'.")

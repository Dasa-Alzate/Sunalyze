"""Parser y evaluador de expresiones de plantilla.

No usa Jinja, `eval`, `exec`, `compile` ni `getattr` dinámico sobre objetos arbitrarios.
El interior de cada `{{ ... }}` es un *pipeline*:

    expr ( '|' filtro ( '(' args ')' )? )*

donde `expr` es una ruta de variable (`panel.power`), un literal, o una expresión aritmética
sobre números, rutas y los operadores `+ - * / ( )` más las funciones `round` y `sum`. La
evaluación aritmética usa un algoritmo shunting-yard propio: nunca se evalúa código.
"""

import math
import re
from functools import lru_cache

from .errors import TemplateError
from .tokenizer import tokenize, Token
from .filters import apply_filter

_PLACEHOLDER_RE = re.compile(r'\{\{(.*?)\}\}', re.DOTALL)

_PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2}
_FUNCTIONS = {'round', 'sum'}
_MAX_DEPTH = 32


class ParsedExpression:
    """Pipeline ya parseado: una expresión base + una cadena de filtros."""

    __slots__ = ('atoms', 'filters', 'is_path')

    def __init__(self, atoms, filters, is_path):
        self.atoms = atoms
        self.filters = filters
        self.is_path = is_path


def _split_pipeline(tokens):
    segments = [[]]
    for tok in tokens:
        if tok.kind == 'pipe':
            segments.append([])
        else:
            segments[-1].append(tok)
    return segments


def _parse_filter(segment):
    if not segment or segment[0].kind != 'name':
        raise TemplateError('Se esperaba el nombre de un filtro tras "|".')
    name = segment[0].value
    if '.' in name:
        raise TemplateError(f"Nombre de filtro inválido: '{name}'.")
    args = []
    rest = segment[1:]
    if rest:
        if rest[0].kind != 'lparen' or rest[-1].kind != 'rparen':
            raise TemplateError(f"Argumentos de filtro mal formados en '{name}'.")
        for tok in rest[1:-1]:
            if tok.kind == 'comma':
                continue
            if tok.kind == 'number':
                args.append(float(tok.value) if '.' in tok.value else int(tok.value))
            elif tok.kind == 'string':
                args.append(tok.value)
            else:
                raise TemplateError(
                    f"Argumento inválido para el filtro '{name}'."
                )
    return (name, args)


def _is_arithmetic(atoms):
    for tok in atoms:
        if tok.kind in ('op', 'lparen', 'rparen', 'comma'):
            return True
        if tok.kind == 'name' and tok.value in _FUNCTIONS:
            return True
    return False


@lru_cache(maxsize=1024)
def parse_expression(source):
    """Parsea el interior de un `{{ ... }}` a un ParsedExpression.

    Cacheado: una expresión es puramente sintáctica (no depende de datos de tenant) y el
    `ParsedExpression` resultante es de solo lectura durante `evaluate`, así que reusarlo entre
    renders es seguro y evita re-tokenizar cada `{{ ... }}` en cada documento. `lru_cache` no
    cachea excepciones, de modo que una expresión inválida vuelve a lanzar `TemplateError`.
    """
    tokens = tokenize(source)
    if not tokens:
        raise TemplateError('Expresión vacía.')
    segments = _split_pipeline(tokens)
    base = segments[0]
    if not base:
        raise TemplateError('Falta la expresión antes del primer filtro.')
    filters = [_parse_filter(seg) for seg in segments[1:]]
    is_path = (
        len(base) == 1 and base[0].kind == 'name' and base[0].value not in _FUNCTIONS
    ) or (len(base) == 1 and base[0].kind in ('string', 'number'))
    if is_path:
        return ParsedExpression(base, filters, is_path=True)
    if not _is_arithmetic(base) and len(base) > 1:
        raise TemplateError('Expresión no reconocida.')
    return ParsedExpression(base, filters, is_path=False)


def _resolve_atom(tok, resolver):
    if tok.kind == 'number':
        return float(tok.value) if '.' in tok.value else int(tok.value)
    if tok.kind == 'string':
        return tok.value
    if tok.kind == 'name':
        return resolver.resolve(tok.value)
    raise TemplateError('Átomo no evaluable.')


def _to_number(value):
    if isinstance(value, bool):
        raise TemplateError('No se puede operar aritméticamente con un booleano.')
    if isinstance(value, (int, float)):
        number = value
    elif isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            raise TemplateError(f"Valor no numérico en cálculo: '{value}'.")
    else:
        raise TemplateError('Valor no numérico en cálculo.')
    if isinstance(number, float) and not math.isfinite(number):
        raise TemplateError('Valor numérico no finito en cálculo.')
    return number


def _apply_op(op, left, right):
    left = _to_number(left)
    right = _to_number(right)
    if op == '+':
        return left + right
    if op == '-':
        return left - right
    if op == '*':
        return left * right
    if op == '/':
        if right == 0:
            raise TemplateError('División por cero.')
        return left / right
    raise TemplateError(f"Operador no soportado: '{op}'.")


def _eval_function(name, args):
    if name == 'round':
        if not args:
            raise TemplateError('round() requiere al menos un argumento.')
        ndigits = int(args[1]) if len(args) > 1 else 0
        return round(_to_number(args[0]), ndigits)
    if name == 'sum':
        return sum(_to_number(a) for a in args)
    raise TemplateError(f"Función no soportada: '{name}'.")


def _eval_arithmetic(atoms, resolver, depth=0):
    if depth > _MAX_DEPTH:
        raise TemplateError('Expresión demasiado anidada.')
    output = []
    operators = []

    def reduce_op():
        op = operators.pop()
        if len(output) < 2:
            raise TemplateError('Expresión aritmética mal formada.')
        right = output.pop()
        left = output.pop()
        output.append(_apply_op(op, left, right))

    index = 0
    n = len(atoms)
    while index < n:
        tok = atoms[index]
        if tok.kind in ('number', 'string'):
            output.append(_resolve_atom(tok, resolver))
        elif tok.kind == 'name':
            if tok.value in _FUNCTIONS:
                if index + 1 >= n or atoms[index + 1].kind != 'lparen':
                    raise TemplateError(f"Se esperaba '(' tras '{tok.value}'.")
                inner, consumed = _collect_call_args(atoms, index + 1, resolver, depth)
                output.append(_eval_function(tok.value, inner))
                index += consumed + 2
                continue
            output.append(resolver.resolve(tok.value))
        elif tok.kind == 'op':
            while (
                operators
                and operators[-1] != '('
                and _PRECEDENCE.get(operators[-1], 0) >= _PRECEDENCE[tok.value]
            ):
                reduce_op()
            operators.append(tok.value)
        elif tok.kind == 'lparen':
            operators.append('(')
        elif tok.kind == 'rparen':
            while operators and operators[-1] != '(':
                reduce_op()
            if not operators:
                raise TemplateError('Paréntesis desbalanceados.')
            operators.pop()
        else:
            raise TemplateError('Token inesperado en cálculo.')
        index += 1

    while operators:
        if operators[-1] == '(':
            raise TemplateError('Paréntesis desbalanceados.')
        reduce_op()
    if len(output) != 1:
        raise TemplateError('Expresión aritmética mal formada.')
    return output[0]


def _collect_call_args(atoms, lparen_index, resolver, depth):
    depthcount = 0
    args_tokens = []
    current = []
    i = lparen_index
    n = len(atoms)
    while i < n:
        tok = atoms[i]
        if tok.kind == 'lparen':
            depthcount += 1
            if depthcount > 1:
                current.append(tok)
        elif tok.kind == 'rparen':
            depthcount -= 1
            if depthcount == 0:
                if current:
                    args_tokens.append(current)
                values = [_eval_arithmetic(grp, resolver, depth + 1) for grp in args_tokens]
                return values, (i - lparen_index)
            current.append(tok)
        elif tok.kind == 'comma' and depthcount == 1:
            args_tokens.append(current)
            current = []
        else:
            current.append(tok)
        i += 1
    raise TemplateError('Llamada a función sin cerrar.')


def evaluate(parsed, resolver):
    """Evalúa un ParsedExpression contra un resolver de variables y aplica los filtros.

    La presentación (locale/currency) se toma del resolver, de modo que los filtros
    numéricos y de moneda formatean según la jurisdicción de la plantilla.
    """
    if parsed.is_path:
        value = _resolve_atom(parsed.atoms[0], resolver)
    else:
        value = _eval_arithmetic(parsed.atoms, resolver)
    presentation = getattr(resolver, 'presentation', None)
    for name, args in parsed.filters:
        value = apply_filter(name, value, args, presentation=presentation)
    return value


def render_text(text, resolver, on_error='placeholder'):
    """Sustituye cada `{{ ... }}` de `text` por su valor resuelto.

    `on_error='placeholder'` deja un marcador legible y nunca propaga (modo render seguro);
    `on_error='raise'` propaga TemplateError (modo validación/preview estricto).
    """
    if not text:
        return ''

    def _sub(match):
        expr = match.group(1).strip()
        try:
            parsed = parse_expression(expr)
            value = evaluate(parsed, resolver)
            return _stringify(value)
        except TemplateError as exc:
            if on_error == 'raise':
                raise TemplateError(f"en «{{{{ {expr} }}}}»: {exc}") from exc
            return f'[{expr}]'

    return _PLACEHOLDER_RE.sub(_sub, text)


def _stringify(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Sí' if value else 'No'
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

"""Tokenizador de expresiones de plantilla. Gramática restringida, sin ejecución.

Reconoce números, strings entre comillas, identificadores (rutas con punto), operadores
aritméticos, paréntesis, coma y la barra de pipeline. Rechaza de raíz cualquier identificador
peligroso (dunders o prefijo de guion bajo), de modo que `__class__`, `__globals__`,
`__mro__`, etc. nunca llegan a parsearse ni a resolverse.
"""

import re

from .errors import TemplateError

MAX_EXPRESSION_LENGTH = 500

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<number>\d+\.\d+|\.\d+|\d+)
  | (?P<string>'[^']*'|"[^"]*")
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)
  | (?P<pipe>\|)
  | (?P<op>[+\-*/])
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<comma>,)
    """,
    re.VERBOSE,
)


class Token:
    __slots__ = ('kind', 'value')

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f'Token({self.kind!r}, {self.value!r})'


def _reject_unsafe_name(name):
    for part in name.split('.'):
        if not part:
            raise TemplateError(f"Nombre inválido en la expresión: '{name}'.")
        if part.startswith('_') or '__' in part:
            raise TemplateError(
                f"Acceso prohibido a atributo interno: '{name}'."
            )


def tokenize(source):
    """Convierte el interior de un `{{ ... }}` en una lista de tokens.

    Lanza TemplateError ante caracteres no reconocidos, expresiones demasiado largas o
    identificadores que apunten a atributos internos (dunders / guion bajo inicial).
    """
    if source is None:
        raise TemplateError('Expresión vacía.')
    if len(source) > MAX_EXPRESSION_LENGTH:
        raise TemplateError('Expresión demasiado larga.')

    tokens = []
    pos = 0
    length = len(source)
    while pos < length:
        match = _TOKEN_RE.match(source, pos)
        if not match:
            raise TemplateError(
                f"Carácter no permitido en la expresión: '{source[pos]}'."
            )
        pos = match.end()
        kind = match.lastgroup
        value = match.group()
        if kind == 'ws':
            continue
        if kind == 'name':
            _reject_unsafe_name(value)
        if kind == 'string':
            value = value[1:-1]
        tokens.append(Token(kind, value))
    return tokens

"""Motor de plantillas de documentos: parser propio seguro, sin Flask ni eval.

Expone el render de plantillas y el catálogo de variables por tipo de documento.
"""

from .errors import TemplateError
from .filters import FILTERS, apply_filter
from .parser import parse_expression, render_text
from .context import build_context, ContextResolver
from .catalog import variable_catalog, VARIABLE_CATALOG
from .renderer import render_section, render_version

__all__ = [
    'TemplateError',
    'FILTERS',
    'apply_filter',
    'parse_expression',
    'render_text',
    'build_context',
    'ContextResolver',
    'variable_catalog',
    'VARIABLE_CATALOG',
    'render_section',
    'render_version',
]

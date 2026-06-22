"""Renderer: TemplateVersion + Project -> HTML por secciones.

Resuelve cada `{{ ... }}` del cuerpo de cada sección contra el contexto del proyecto, aplica
los filtros y devuelve HTML escapado, listo para el pipeline WeasyPrint existente. La salida
escapa tanto el texto verbatim como los valores resueltos (defensa contra XSS almacenado).
"""

from html import escape

from .errors import TemplateError
from .parser import _PLACEHOLDER_RE, parse_expression, evaluate, _stringify
from .context import build_context, ContextResolver


def _render_body(body, resolver, on_error):
    if not body:
        return ''
    out = []
    last = 0
    for match in _PLACEHOLDER_RE.finditer(body):
        out.append(escape(body[last:match.start()]))
        expr = match.group(1).strip()
        try:
            parsed = parse_expression(expr)
            value = evaluate(parsed, resolver)
            out.append(escape(_stringify(value)))
        except TemplateError:
            if on_error == 'raise':
                raise
            out.append(escape(f'[{expr}]'))
        last = match.end()
    out.append(escape(body[last:]))
    text = ''.join(out)
    return text.replace('\n', '<br>')


def render_section(section, resolver, on_error='placeholder'):
    """Renderiza una sección {id, type, title, body} a un dict con HTML resuelto."""
    title = section.get('title') or ''
    body = section.get('body') or ''
    return {
        'id': section.get('id'),
        'type': section.get('type') or 'text',
        'title': _render_body(title, resolver, on_error),
        'body': _render_body(body, resolver, on_error),
    }


def render_version(version_content, project, user=None, org=None, on_error='placeholder'):
    """Renderiza la lista ordenada de secciones de un TemplateVersion contra un Project.

    Devuelve {'sections': [...], 'html': '...'} donde cada sección lleva su HTML resuelto y
    `html` es el documento ensamblado, listo para WeasyPrint.
    """
    sections = version_content if isinstance(version_content, list) else (
        version_content.get('sections', []) if isinstance(version_content, dict) else []
    )
    context = build_context(project, user=user, org=org)
    resolver = ContextResolver(context)
    rendered = [render_section(s, resolver, on_error) for s in sections]
    html = _assemble_html(rendered)
    return {'sections': rendered, 'html': html}


def _assemble_html(sections):
    parts = []
    for s in sections:
        parts.append('<section class="tpl-section">')
        if s['title']:
            parts.append(f'<h2>{s["title"]}</h2>')
        if s['body']:
            parts.append(f'<div class="tpl-body">{s["body"]}</div>')
        parts.append('</section>')
    return '\n'.join(parts)

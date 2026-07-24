
from html import escape

from .errors import TemplateError
from .parser import _PLACEHOLDER_RE, parse_expression, evaluate, _stringify
from .context import build_context, ContextResolver
from .sanitizer import sanitize_html


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
        except TemplateError as exc:
            if on_error == 'raise':
                raise TemplateError(f"en «{{{{ {expr} }}}}»: {exc}") from exc
            out.append(escape(f'[{expr}]'))
        last = match.end()
    out.append(escape(body[last:]))
    text = ''.join(out)
    return text.replace('\n', '<br>')


def _resolve_placeholders(data, resolver, on_error):
    out = []
    last = 0
    for match in _PLACEHOLDER_RE.finditer(data):
        out.append(escape(data[last:match.start()]))
        expr = match.group(1).strip()
        try:
            parsed = parse_expression(expr)
            value = evaluate(parsed, resolver)
            out.append(escape(_stringify(value)))
        except TemplateError as exc:
            if on_error == 'raise':
                raise TemplateError(f"en «{{{{ {expr} }}}}»: {exc}") from exc
            out.append(escape(f'[{expr}]'))
        last = match.end()
    out.append(escape(data[last:]))
    return ''.join(out)


def _render_richdoc(html, resolver, on_error):
    return sanitize_html(html, lambda data: _resolve_placeholders(data, resolver, on_error))


def render_section(section, resolver, on_error='placeholder'):
    stype = section.get('type') or 'text'
    if stype == 'richdoc':
        return {
            'id': section.get('id'),
            'type': 'richdoc',
            'html': _render_richdoc(section.get('html') or '', resolver, on_error),
        }
    title = section.get('title') or ''
    body = section.get('body') or ''
    return {
        'id': section.get('id'),
        'type': stype,
        'title': _render_body(title, resolver, on_error),
        'body': _render_body(body, resolver, on_error),
    }


def render_version(version_content, project, user=None, org=None, on_error='placeholder',
                   presentation=None):
    sections = version_content if isinstance(version_content, list) else (
        version_content.get('sections', []) if isinstance(version_content, dict) else []
    )
    context = build_context(project, user=user, org=org)
    resolver = ContextResolver(context, presentation=presentation)
    rendered = [render_section(s, resolver, on_error) for s in sections]
    html = _assemble_html(rendered)
    return {'sections': rendered, 'html': html}


def _assemble_html(sections):
    parts = []
    for s in sections:
        if s.get('type') == 'richdoc':
            parts.append(f'<section class="tpl-section tpl-richdoc">{s.get("html", "")}</section>')
            continue
        parts.append('<section class="tpl-section">')
        if s['title']:
            parts.append(f'<h2>{s["title"]}</h2>')
        if s['body']:
            parts.append(f'<div class="tpl-body">{s["body"]}</div>')
        parts.append('</section>')
    return '\n'.join(parts)

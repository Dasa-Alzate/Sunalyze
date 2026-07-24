"""Sanitizador de HTML de lista blanca para el editor de plantillas v2.

El editor WYSIWYG (contentEditable) produce HTML arbitrario al pegar, así que el
servidor nunca confía en él: se reparsea con la stdlib y solo se conservan las
etiquetas y atributos permitidos. En la misma pasada se reemplazan los
marcadores `{{ expr }}` sobre los nodos de texto (nunca sobre etiquetas), de modo
que el resultado es HTML seguro con las variables ya evaluadas.
"""

from html import escape
from html.parser import HTMLParser

ALLOWED = {
    'h2': set(), 'h3': set(), 'h4': set(),
    'p': set(), 'strong': set(), 'b': set(), 'em': set(), 'i': set(), 'u': set(),
    'ul': set(), 'ol': set(), 'li': set(), 'br': set(),
    'table': set(), 'thead': set(), 'tbody': set(), 'tr': set(),
    'th': {'colspan', 'rowspan'}, 'td': {'colspan', 'rowspan'},
    'img': {'src', 'alt'},
    'span': {'class'},
}
VOID = {'br', 'img'}
DROP_WITH_CONTENT = {'script', 'style'}


def _safe_img_src(src):
    if not src:
        return None
    s = src.strip()
    if s.startswith('//'):
        return None
    if s.startswith('/') or s.startswith('data:image/'):
        return s
    return None


class _Sanitizer(HTMLParser):

    def __init__(self, on_text):
        super().__init__(convert_charrefs=True)
        self.out = []
        self._on_text = on_text
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self._skip += 1
            return
        if self._skip:
            return
        spec = ALLOWED.get(tag)
        if spec is None:
            return
        rendered = []
        for key, value in attrs:
            if key not in spec:
                continue
            if tag == 'img' and key == 'src':
                value = _safe_img_src(value)
                if value is None:
                    return
            rendered.append(f' {key}="{escape(value or "", quote=True)}"')
        attr_str = ''.join(rendered)
        self.out.append(f'<{tag}{attr_str}/>' if tag in VOID else f'<{tag}{attr_str}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        if tag in ALLOWED and tag not in VOID:
            self.out.append(f'</{tag}>')

    def handle_data(self, data):
        if self._skip:
            return
        self.out.append(self._on_text(data))


def sanitize_html(html, on_text):
    parser = _Sanitizer(on_text)
    parser.feed(html or '')
    parser.close()
    return ''.join(parser.out)

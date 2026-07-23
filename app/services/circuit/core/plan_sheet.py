import re
from xml.sax.saxutils import escape

SHEET_PORTRAIT = (794, 1123)
SHEET_LANDSCAPE = (1123, 794)
MARGIN = 18
FRAME_GAP = 6
BLOCK_H = 96
NORMS = 'Conforme a REBT ITC-BT-40 · UNE-HD 60364-7-712 · RD 244/2019'
DEFAULT_FIELDS = (
    ('Instaladora', ''),
    ('Fecha', ''),
    ('Firma y sello', ''),
    ('Nº instalación', ''),
)

_OPEN_TAG = re.compile(r'<svg\b[^>]*>', re.S)
_VIEWBOX = re.compile(r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"')


def _inner_parts(svg):
    m = _OPEN_TAG.search(svg)
    vb = _VIEWBOX.search(m.group(0))
    x, y, w, h = (float(v) for v in vb.groups())
    content = svg[m.end():svg.rfind('</svg>')]
    return (x, y, w, h), content


def _text(x, y, s, size, color='#131316', anchor='middle', weight=''):
    w = f' font-weight="{weight}"' if weight else ''
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="monospace"'
        f' font-size="{size}" fill="{color}"{w}>{escape(str(s))}</text>'
    )


def _line(x1, y1, x2, y2, width=1):
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
        f' stroke="#131316" stroke-width="{width}"/>'
    )


def wrap_plan_sheet(svg, *, title, orientation='portrait', norms=NORMS, fields=None):
    W, H = SHEET_LANDSCAPE if orientation == 'landscape' else SHEET_PORTRAIT
    fields = list(fields) if fields else list(DEFAULT_FIELDS)
    (vx, vy, vw, vh), content = _inner_parts(svg)

    fx1, fy1 = MARGIN, MARGIN
    fx2, fy2 = W - MARGIN, H - MARGIN
    ix1, iy1 = fx1 + FRAME_GAP, fy1 + FRAME_GAP
    ix2, iy2 = fx2 - FRAME_GAP, fy2 - FRAME_GAP

    block_y = iy2 - BLOCK_H
    area_pad = 10
    ax, ay = ix1 + area_pad, iy1 + area_pad
    aw = (ix2 - ix1) - 2 * area_pad
    ah = (block_y - iy1) - 2 * area_pad

    scale = min(aw / vw, ah / vh, 1.15)
    dw, dh = vw * scale, vh * scale
    dx = ax + (aw - dw) / 2
    dy = ay + (ah - dh) / 2

    parts = [
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
        f'<rect x="{fx1}" y="{fy1}" width="{fx2 - fx1}" height="{fy2 - fy1}"'
        f' fill="none" stroke="#131316" stroke-width="2"/>',
        f'<rect x="{ix1}" y="{iy1}" width="{ix2 - ix1}" height="{iy2 - iy1}"'
        f' fill="none" stroke="#131316" stroke-width="1"/>',
        f'<svg x="{round(dx, 1)}" y="{round(dy, 1)}" width="{round(dw, 1)}" height="{round(dh, 1)}"'
        f' viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="xMidYMid meet">{content}</svg>',
        _line(ix1, block_y, ix2, block_y, 1),
    ]

    cx = (ix1 + ix2) / 2
    title_h = 40
    norms_h = 22
    parts.append(_text(cx, block_y + 26, title, 16, weight='bold'))
    parts.append(_line(ix1, block_y + title_h, ix2, block_y + title_h))
    parts.append(_text(cx, block_y + title_h + 15, norms, 10, color='#444444'))
    fields_y = block_y + title_h + norms_h
    parts.append(_line(ix1, fields_y, ix2, fields_y))

    n = len(fields)
    col_w = (ix2 - ix1) / n
    for i, (label, value) in enumerate(fields):
        x0 = ix1 + i * col_w
        if i:
            parts.append(_line(x0, fields_y, x0, iy2))
        parts.append(_text(x0 + 8, fields_y + 13, f'{label}:', 8, color='#666666', anchor='start'))
        if value:
            parts.append(_text(x0 + 8, fields_y + 27, value, 10, anchor='start'))

    body = '\n  '.join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
        f' viewBox="0 0 {W} {H}">\n  {body}\n</svg>'
    )


def fit_to_mm(svg, max_w_mm, max_h_mm):
    m = _OPEN_TAG.search(svg)
    vb = _VIEWBOX.search(m.group(0))
    _, _, vw, vh = (float(v) for v in vb.groups())
    scale = min(max_w_mm / vw, max_h_mm / vh)
    w_mm = round(vw * scale, 1)
    h_mm = round(vh * scale, 1)
    open_tag = m.group(0)
    open_tag = re.sub(r'\swidth="[^"]*"', f' width="{w_mm}mm"', open_tag, count=1)
    open_tag = re.sub(r'\sheight="[^"]*"', f' height="{h_mm}mm"', open_tag, count=1)
    return svg[:m.start()] + open_tag + svg[m.end():]

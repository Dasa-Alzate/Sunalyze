
import math

CURVE = '#123a63'
POWER = '#d9920a'
GRID = '#e1dfdd'
AXIS = '#8a8886'
INK = '#242424'
MUTED = '#616161'
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"


def _coefficients(voc, vmp, imp, isc):
    ratio = imp / isc
    if not 0 < ratio < 1:
        return None
    c2 = (vmp / voc - 1.0) / math.log(1.0 - ratio)
    if c2 <= 0:
        return None
    c1 = (1.0 - ratio) * math.exp(-vmp / (c2 * voc))
    return c1, c2


def current_at(v, voc, isc, c1, c2):
    try:
        value = isc * (1.0 - c1 * (math.exp(v / (c2 * voc)) - 1.0))
    except OverflowError:
        return 0.0
    return max(0.0, value)


def samples(voc, vmp, imp, isc, steps=90):
    coeff = _coefficients(voc, vmp, imp, isc)
    if coeff is None:
        return []
    c1, c2 = coeff
    points = []
    for i in range(steps + 1):
        v = voc * i / steps
        points.append((v, current_at(v, voc, isc, c1, c2)))
    return points


def render(voc, vmp, imp, isc, width=430, height=280,
           irradiances=(1000, 800, 600, 400)):
    curve = samples(voc, vmp, imp, isc)
    if not curve:
        return ''

    pad_l, pad_r, pad_t, pad_b = 46, 46, 18, 34
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    v_max = math.ceil(voc / 10) * 10
    i_max = math.ceil(isc * 1.15)
    p_max = max(v * i for v, i in curve) or 1.0

    def sx(v):
        return pad_l + v / v_max * plot_w

    def sy_i(i):
        return pad_t + plot_h - i / i_max * plot_h

    def sy_p(p):
        return pad_t + plot_h - p / p_max * plot_h

    parts = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>']

    for k in range(0, i_max + 1, max(1, i_max // 5)):
        y = sy_i(k)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}"'
                     f' stroke="{GRID}" stroke-width="0.8"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 3.5:.1f}" text-anchor="end"'
                     f' font-family="{FONT}" font-size="9" fill="{MUTED}">{k}</text>')
    step_v = 10 if v_max <= 60 else 20
    for v in range(0, v_max + 1, step_v):
        x = sx(v)
        parts.append(f'<line x1="{x:.1f}" y1="{pad_t}" x2="{x:.1f}" y2="{pad_t + plot_h}"'
                     f' stroke="{GRID}" stroke-width="0.8"/>')
        parts.append(f'<text x="{x:.1f}" y="{pad_t + plot_h + 14}" text-anchor="middle"'
                     f' font-family="{FONT}" font-size="9" fill="{MUTED}">{v}</text>')

    for g in irradiances[1:]:
        factor = g / irradiances[0]
        pts = ' '.join(f'{sx(v):.1f},{sy_i(i * factor):.1f}' for v, i in curve)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{CURVE}"'
                     f' stroke-width="1" opacity="0.3"/>')
        gy = sy_i(isc * factor)
        parts.append(f'<text x="{sx(voc * 0.30):.1f}" y="{gy - 3.5:.1f}"'
                     f' font-family="{FONT}" font-size="7.5" fill="{CURVE}"'
                     f' opacity="0.65">{g}</text>')
    parts.append(f'<text x="{sx(voc * 0.30):.1f}" y="{sy_i(isc) - 15:.1f}"'
                 f' font-family="{FONT}" font-size="7.5" fill="{CURVE}"'
                 f' opacity="0.75">W/m²</text>')

    p_pts = ' '.join(f'{sx(v):.1f},{sy_p(v * i):.1f}' for v, i in curve)
    parts.append(f'<polyline points="{p_pts}" fill="none" stroke="{POWER}"'
                 f' stroke-width="1.6" stroke-dasharray="4 3"/>')

    pts = ' '.join(f'{sx(v):.1f},{sy_i(i):.1f}' for v, i in curve)
    parts.append(f'<polyline points="{pts}" fill="none" stroke="{CURVE}"'
                 f' stroke-width="2.2" stroke-linejoin="round"/>')

    mx, my = sx(vmp), sy_i(imp)
    parts.append(f'<line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{pad_t + plot_h}"'
                 f' stroke="{POWER}" stroke-width="0.9" stroke-dasharray="2 3"/>')
    parts.append(f'<line x1="{pad_l}" y1="{my:.1f}" x2="{mx:.1f}" y2="{my:.1f}"'
                 f' stroke="{POWER}" stroke-width="0.9" stroke-dasharray="2 3"/>')
    parts.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="4" fill="#ffffff"'
                 f' stroke="{POWER}" stroke-width="2"/>')
    parts.append(f'<text x="{mx + 8:.1f}" y="{my - 8:.1f}" font-family="{FONT}"'
                 f' font-size="9.5" font-weight="600" fill="{INK}">MPP</text>')

    parts.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}"'
                 f' y2="{pad_t + plot_h}" stroke="{AXIS}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}"'
                 f' stroke="{AXIS}" stroke-width="1.2"/>')
    parts.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{height - 4}" text-anchor="middle"'
                 f' font-family="{FONT}" font-size="9.5" fill="{MUTED}">Tensión (V)</text>')
    parts.append(f'<text x="12" y="{pad_t + plot_h / 2:.1f}" text-anchor="middle"'
                 f' font-family="{FONT}" font-size="9.5" fill="{MUTED}"'
                 f' transform="rotate(-90 12 {pad_t + plot_h / 2:.1f})">Corriente (A)</text>')
    parts.append(f'<text x="{width - 12}" y="{pad_t + plot_h / 2:.1f}" text-anchor="middle"'
                 f' font-family="{FONT}" font-size="9.5" fill="{POWER}"'
                 f' transform="rotate(90 {width - 12} {pad_t + plot_h / 2:.1f})">Potencia</text>')

    body = '\n  '.join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
            f' viewBox="0 0 {width} {height}" role="img"'
            f' aria-label="Curva corriente-tensión del módulo a distintas irradiancias">'
            f'\n  {body}\n</svg>')

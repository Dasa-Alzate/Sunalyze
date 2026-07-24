"""Diagrama de trayectoria solar para la memoria técnica.

Reconstruye de forma determinista (SVG) el recorrido aparente del sol sobre la
instalación en verano e invierno, con los ángulos reales derivados de la
latitud del proyecto (elevación solar al mediodía en cada solsticio y equinoccio)
y la inclinación/azimut del campo fotovoltaico. Pensado también como widget
reutilizable en otras plantillas (propuesta al cliente, etc.).
"""

import math

OBLIQUITY = 23.45

SKY = '#eaf3fb'
GROUND = '#dfe7ee'
INK = '#1f2937'
MUTED = '#6b7280'
SUN = '#f6c945'
SUN_STROKE = '#e0a800'
PANEL = '#12335c'
ROOF = '#c9a06a'
WALL = '#e7d6bb'
SUMMER = '#e0a800'
WINTER = '#5b8bd0'


def _noon_elevation(lat, declination):
    return 90 - abs(lat) + declination


class SolarPathService:

    @staticmethod
    def generate(lat, tilt=None, azimuth=None):
        lat = float(lat)
        summer = round(_noon_elevation(lat, OBLIQUITY))
        equinox = round(_noon_elevation(lat, 0))
        winter = max(1, round(_noon_elevation(lat, -OBLIQUITY)))

        W, H = 660, 460
        cx, cy = 330, 312
        rx, ry = 288, 70
        max_lift = 214

        ex, ey = cx + rx, cy
        wx, wy = cx - rx, cy

        def peak_y(elev):
            return cy - ry - (max(0, elev) / 90.0) * max_lift

        def arc_point(elev, t):
            py = peak_y(elev)
            cp_y = 2 * py - cy
            mt = 1 - t
            x = mt * mt * ex + 2 * mt * t * cx + t * t * wx
            y = mt * mt * ey + 2 * mt * t * cp_y + t * t * wy
            return x, y

        def arc(elev, color, width, dash=''):
            py = peak_y(elev)
            da = f' stroke-dasharray="{dash}"' if dash else ''
            return (f'<path d="M {ex} {ey} Q {cx} {2 * py - cy:.1f} {wx} {wy}"'
                    f' fill="none" stroke="{color}" stroke-width="{width}"{da}/>')

        parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']

        parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{GROUND}"'
                     f' fill-opacity="0.5" stroke="{MUTED}" stroke-width="1.5"/>')
        parts.append(f'<line x1="{wx}" y1="{cy}" x2="{ex}" y2="{cy}" stroke="{MUTED}"'
                     f' stroke-width="1" stroke-dasharray="4 4"/>')
        parts.append(f'<line x1="{cx}" y1="{cy - ry}" x2="{cx}" y2="{cy + ry}" stroke="{MUTED}"'
                     f' stroke-width="1" stroke-dasharray="4 4"/>')

        parts.append(arc(equinox, MUTED, 1.5, dash='2 5'))
        parts.append(arc(winter, WINTER, 2.5, dash='9 6'))
        parts.append(arc(summer, SUMMER, 2.5, dash='9 6'))

        sx, sy = arc_point(summer, 0.16)
        parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="20" fill="{SUN}" stroke="{SUN_STROKE}" stroke-width="2"/>')
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1 = sx + 24 * math.cos(rad)
            y1 = sy + 24 * math.sin(rad)
            x2 = sx + 32 * math.cos(rad)
            y2 = sy + 32 * math.sin(rad)
            parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
                         f' stroke="{SUN_STROKE}" stroke-width="2"/>')

        parts.append(SolarPathService._house(cx, cy - 8, tilt))

        def label(x, y, text, size=15, color=INK, weight='normal', anchor='middle'):
            return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="monospace"'
                    f' font-size="{size}" font-weight="{weight}" fill="{color}">{text}</text>')

        parts.append(label(cx, cy - ry - 8, 'N', 16, MUTED, 'bold'))
        parts.append(label(cx, cy + ry + 22, 'S', 16, MUTED, 'bold'))
        parts.append(label(ex + 16, cy + 5, 'E', 16, MUTED, 'bold'))
        parts.append(label(wx - 16, cy + 5, 'O', 16, MUTED, 'bold'))

        vpx, vpy = arc_point(summer, 0.5)
        parts.append(label(vpx, vpy - 12, f'Verano · {summer}°', 15, SUN_STROKE, 'bold'))
        ipx, ipy = arc_point(winter, 0.5)
        parts.append(label(ipx, ipy - 12, f'Invierno · {winter}°', 15, WINTER, 'bold'))

        note = f'Elevación solar al mediodía (lat {abs(lat):.1f}°): verano {summer}° · equinoccio {equinox}° · invierno {winter}°'
        parts.append(label(cx, H - 34, note, 13, MUTED))
        if tilt is not None or azimuth is not None:
            bits = []
            if tilt is not None:
                bits.append(f'inclinación β = {round(float(tilt))}°')
            if azimuth is not None:
                bits.append(f'azimut {round(float(azimuth))}° ({SolarPathService._orientation(azimuth)})')
            parts.append(label(cx, H - 14, 'Campo fotovoltaico: ' + ' · '.join(bits), 13, INK))

        body = '\n  '.join(parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
                f' viewBox="0 0 {W} {H}">\n  {body}\n</svg>')

    @staticmethod
    def _orientation(azimuth):
        a = float(azimuth) % 360
        dirs = [(0, 'Norte'), (45, 'NE'), (90, 'Este'), (135, 'SE'), (180, 'Sur'),
                (225, 'SO'), (270, 'Oeste'), (315, 'NO'), (360, 'Norte')]
        return min(dirs, key=lambda d: abs(d[0] - a))[1]

    @staticmethod
    def _house(cx, cy, tilt):
        bw, bh = 120, 66
        x0 = cx - bw / 2
        y0 = cy
        parts = [
            f'<rect x="{x0}" y="{y0}" width="{bw}" height="{bh}" fill="{WALL}"'
            f' stroke="{INK}" stroke-width="1.5"/>',
            f'<rect x="{x0 + 16}" y="{y0 + 22}" width="20" height="24" fill="#bcd3ea" stroke="{INK}" stroke-width="1"/>',
            f'<rect x="{x0 + 84}" y="{y0 + 22}" width="20" height="24" fill="#bcd3ea" stroke="{INK}" stroke-width="1"/>',
            f'<rect x="{x0 + 50}" y="{y0 + 30}" width="20" height="{bh - 30}" fill="#9a7b52" stroke="{INK}" stroke-width="1"/>',
        ]
        tilt_deg = float(tilt) if tilt is not None else 25.0
        tilt_deg = max(5.0, min(45.0, tilt_deg))
        roof_w = bw + 22
        rx0 = cx - roof_w / 2
        ridge = 40 * math.sin(math.radians(tilt_deg))
        ry0 = y0
        parts.append(
            f'<polygon points="{rx0:.1f},{ry0:.1f} {rx0 + roof_w:.1f},{ry0:.1f}'
            f' {cx + roof_w / 2 - 14:.1f},{ry0 - ridge:.1f} {cx - roof_w / 2 + 14:.1f},{ry0 - ridge:.1f}"'
            f' fill="{ROOF}" stroke="{INK}" stroke-width="1.5"/>'
        )
        pw, gap = 22, 4
        for i in range(3):
            px = rx0 + 16 + i * (pw + gap)
            parts.append(f'<rect x="{px:.1f}" y="{ry0 - ridge + 4:.1f}" width="{pw}" height="{ridge + 4:.1f}"'
                         f' fill="{PANEL}" stroke="#dbe4ee" stroke-width="1"/>')

        hx = rx0 + roof_w + 6
        parts.append(f'<line x1="{hx}" y1="{ry0}" x2="{hx + 40}" y2="{ry0}" stroke="{MUTED}"'
                     f' stroke-width="1" stroke-dasharray="3 3"/>')
        parts.append(f'<path d="M {hx + 30} {ry0} A 30 30 0 0 0 {hx + 30 - 30 * math.cos(math.radians(tilt_deg)):.1f}'
                     f' {ry0 - 30 * math.sin(math.radians(tilt_deg)):.1f}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        parts.append(f'<text x="{hx + 34}" y="{ry0 - 6}" font-family="monospace" font-size="12" fill="{INK}">β</text>')
        return '<g>' + ''.join(parts) + '</g>'

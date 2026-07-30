
import math

from app.services import solar_geometry as sg

INK = '#242424'
BODY = '#424242'
MUTED = '#616161'
FAINT = '#bdbdbd'
HAIRLINE = '#e1dfdd'
SURFACE = '#ffffff'
GROUND_FILL = '#f3f2f1'
GROUND_EDGE = '#d1d1d1'

SUMMER = '#d9920a'
WINTER = '#2f6fd0'
EQUINOX = '#8a8886'
SUN_CORE = '#f0c25f'
SUN_EDGE = '#b9770a'

WALL = '#efece7'
WALL_SIDE = '#ddd8d0'
ROOF = '#b9b3aa'
MODULE = '#123a63'
MODULE_EDGE = '#5b7fa6'
SHADOW = '#242424'

W, H = 960, 660
CX, CY = 470, 340
SCALE = 230
PITCH = 64.0
VIEW_AZIMUTH = 342.0
SKY_RADIUS = 1.0

FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"


def _fmt(v):
    return f'{v:.1f}'


class _Camera:

    def __init__(self, view_azimuth=VIEW_AZIMUTH, pitch=PITCH, scale=SCALE,
                 cx=CX, cy=CY):
        a = math.radians(view_azimuth)
        self.sin_a, self.cos_a = math.sin(a), math.cos(a)
        p = math.radians(pitch)
        self.sin_p, self.cos_p = math.sin(p), math.cos(p)
        self.scale, self.cx, self.cy = scale, cx, cy

    def project(self, east, north, up):
        x = east * self.cos_a - north * self.sin_a
        y = east * self.sin_a + north * self.cos_a
        return (self.cx + x * self.scale,
                self.cy - (y * self.sin_p + up * self.cos_p) * self.scale)

    def depth(self, east, north, up):
        return east * self.sin_a + north * self.cos_a


CAM = _Camera()


def _path(points, close=False):
    if not points:
        return ''
    head = f'M {_fmt(points[0][0])} {_fmt(points[0][1])}'
    rest = ' '.join(f'L {_fmt(x)} {_fmt(y)}' for x, y in points[1:])
    return f'{head} {rest}' + (' Z' if close else '')


def _ring(elev_deg, radius=1.0, step=4):
    pts = []
    up = math.sin(math.radians(elev_deg)) * radius
    horiz = math.cos(math.radians(elev_deg)) * radius
    for a in range(0, 361, step):
        rad = math.radians(a)
        pts.append(CAM.project(horiz * math.sin(rad), horiz * math.cos(rad), up))
    return pts


def _text(x, y, content, size=13, color=BODY, weight='400', anchor='middle',
          opacity=None, spacing=None):
    extra = f' opacity="{opacity}"' if opacity is not None else ''
    ls = f' letter-spacing="{spacing}"' if spacing else ''
    return (f'<text x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="{anchor}"'
            f' font-family="{FONT}" font-size="{size}" font-weight="{weight}"'
            f' fill="{color}"{extra}{ls}>{content}</text>')


def _ground():
    disc = _ring(0.0)
    parts = [f'<path d="{_path(disc, close=True)}" fill="{GROUND_FILL}"'
             f' stroke="{GROUND_EDGE}" stroke-width="1.4"/>']
    for elev in (30, 60):
        ring = _ring(elev, SKY_RADIUS)
        parts.append(f'<path d="{_path(ring, close=True)}" fill="none" stroke="{HAIRLINE}"'
                     f' stroke-width="1" stroke-dasharray="3 5"/>')
        rad = math.radians(318)
        lx, ly = CAM.project(SKY_RADIUS * math.cos(math.radians(elev)) * math.sin(rad),
                             SKY_RADIUS * math.cos(math.radians(elev)) * math.cos(rad),
                             SKY_RADIUS * math.sin(math.radians(elev)))
        parts.append(_text(lx - 6, ly, f'{elev}°', 10, FAINT, anchor='end'))
    for a in range(0, 360, 30):
        rad = math.radians(a)
        ex, ey = CAM.project(math.sin(rad), math.cos(rad), 0.0)
        parts.append(f'<line x1="{_fmt(CAM.cx)}" y1="{_fmt(CAM.cy)}" x2="{_fmt(ex)}"'
                     f' y2="{_fmt(ey)}" stroke="{HAIRLINE}" stroke-width="0.8"/>')
    return parts


def _cardinals():
    parts = []
    for label, a in (('N', 0), ('E', 90), ('S', 180), ('O', 270)):
        rad = math.radians(a)
        x, y = CAM.project(1.10 * math.sin(rad), 1.10 * math.cos(rad), 0.0)
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="12" fill="{SURFACE}"'
                     f' stroke="{HAIRLINE}" stroke-width="1"/>')
        parts.append(_text(x, y + 4, label, 12, MUTED, '700'))
    return parts


def _track_path(lat, decl, color, width, dash=None, opacity=1.0):
    pts = [CAM.project(e * SKY_RADIUS, n * SKY_RADIUS, u * SKY_RADIUS)
           for _, e, n, u in sg.sun_track(lat, decl)]
    if len(pts) < 2:
        return ''
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<path d="{_path(pts)}" fill="none" stroke="{color}" stroke-width="{width}"'
            f' stroke-linecap="round" opacity="{opacity}"{da}/>')


def _hour_marks(lat, decl, color, labels=True):
    parts = []
    limit = sg.sunrise_hour_angle(lat, decl)
    for hour in range(4, 21):
        omega = 15.0 * (hour - 12)
        if abs(omega) > limit - 3:
            continue
        east, north, up = sg.sun_vector(lat, decl, omega)
        x, y = CAM.project(east * SKY_RADIUS, north * SKY_RADIUS, up * SKY_RADIUS)
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="2.4" fill="{color}"/>')
        if labels and hour % 3 == 0:
            dx = 13 if east >= 0 else -13
            anchor = 'start' if east >= 0 else 'end'
            parts.append(_text(x + dx, y + 4, f'{hour}h', 10, color, '600', anchor=anchor))
    return parts


def _meridian():
    pts = []
    for a in range(0, 181, 3):
        rad = math.radians(a)
        pts.append(CAM.project(0.0, math.cos(rad), math.sin(rad)))
    zx, zy = CAM.project(0.0, 0.0, 1.0)
    return [f'<path d="{_path(pts)}" fill="none" stroke="{HAIRLINE}" stroke-width="1"'
            f' stroke-dasharray="2 6"/>',
            f'<circle cx="{_fmt(zx)}" cy="{_fmt(zy)}" r="2" fill="{FAINT}"/>',
            _text(zx, zy - 9, 'cenit', 9.5, FAINT)]


def _drop_line(east, north, up, color, opacity=0.5):
    tx, ty = CAM.project(east, north, up)
    gx, gy = CAM.project(east, north, 0.0)
    return [f'<line x1="{_fmt(tx)}" y1="{_fmt(ty)}" x2="{_fmt(gx)}" y2="{_fmt(gy)}"'
            f' stroke="{color}" stroke-width="1" stroke-dasharray="2 4"'
            f' opacity="{opacity}"/>',
            f'<circle cx="{_fmt(gx)}" cy="{_fmt(gy)}" r="2.2" fill="{color}"'
            f' opacity="{opacity + 0.2}"/>']


def _noon_markers(lat, seasons):
    parts = []
    for _label, decl, color in seasons:
        if color == EQUINOX:
            continue
        east, north, up = sg.sun_vector(lat, decl, 0.0)
        if up <= 0.02:
            continue
        parts += _drop_line(east, north, up, color, 0.45)
        x, y = CAM.project(east, north, up)
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="3.6" fill="{SURFACE}"'
                     f' stroke="{color}" stroke-width="2"/>')
    return parts


def _incidence_ray(sun, house):
    sx, sy = CAM.project(sun[0] * SKY_RADIUS, sun[1] * SKY_RADIUS, sun[2] * SKY_RADIUS)
    target = house.array_centre()
    tx, ty = CAM.project(*target)
    return [f'<line x1="{_fmt(sx)}" y1="{_fmt(sy)}" x2="{_fmt(tx)}" y2="{_fmt(ty)}"'
            f' stroke="{SUN_EDGE}" stroke-width="1.2" stroke-dasharray="5 5" opacity="0.55"/>']


def _sun(east, north, up, radius=17):
    x, y = CAM.project(east, north, up)
    parts = [f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{radius + 13}" fill="{SUN_CORE}"'
             f' opacity="0.16"/>',
             f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{radius + 6}" fill="{SUN_CORE}"'
             f' opacity="0.26"/>',
             f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{radius}" fill="{SUN_CORE}"'
             f' stroke="{SUN_EDGE}" stroke-width="1.6"/>']
    for a in range(0, 360, 30):
        rad = math.radians(a)
        parts.append(
            f'<line x1="{_fmt(x + (radius + 6) * math.cos(rad))}"'
            f' y1="{_fmt(y + (radius + 6) * math.sin(rad))}"'
            f' x2="{_fmt(x + (radius + 13) * math.cos(rad))}"'
            f' y2="{_fmt(y + (radius + 13) * math.sin(rad))}"'
            f' stroke="{SUN_EDGE}" stroke-width="1.6" stroke-linecap="round" opacity="0.75"/>')
    return parts


def _rotate(px, py, angle_deg):
    a = math.radians(angle_deg)
    return px * math.cos(a) + py * math.sin(a), -px * math.sin(a) + py * math.cos(a)


class _House:

    def __init__(self, tilt_deg, azimuth_deg, half_w=0.25, half_d=0.17, wall=0.15):
        self.tilt = max(8.0, min(48.0, float(tilt_deg)))
        self.yaw = float(azimuth_deg) - 180.0
        self.hw, self.hd, self.wall = half_w, half_d, wall
        self.ridge = self.wall + self.hd * math.tan(math.radians(self.tilt))

    def _v(self, lx, ly, lz):
        east, north = _rotate(lx, ly, self.yaw)
        return east, north, lz

    def corners(self):
        hw, hd, wall = self.hw, self.hd, self.wall
        return {
            'front_bl': self._v(-hw, -hd, 0.0),
            'front_br': self._v(hw, -hd, 0.0),
            'front_tl': self._v(-hw, -hd, wall),
            'front_tr': self._v(hw, -hd, wall),
            'back_bl': self._v(-hw, hd, 0.0),
            'back_br': self._v(hw, hd, 0.0),
            'back_tl': self._v(-hw, hd, wall),
            'back_tr': self._v(hw, hd, wall),
            'ridge_l': self._v(-hw, 0.0, self.ridge),
            'ridge_r': self._v(hw, 0.0, self.ridge),
        }

    def faces(self):
        c = self.corners()
        return [
            ('back', [c['back_bl'], c['back_br'], c['back_tr'], c['back_tl']], WALL_SIDE),
            ('left', [c['front_bl'], c['back_bl'], c['back_tl'], c['front_tl']], WALL_SIDE),
            ('right', [c['front_br'], c['back_br'], c['back_tr'], c['front_tr']], WALL_SIDE),
            ('front', [c['front_bl'], c['front_br'], c['front_tr'], c['front_tl']], WALL),
            ('roof_back', [c['back_tl'], c['back_tr'], c['ridge_r'], c['ridge_l']], ROOF),
            ('roof_front', [c['front_tl'], c['front_tr'], c['ridge_r'], c['ridge_l']], None),
        ]

    def module_quads(self, cols=4, rows=2, margin=0.018, gap=0.008):
        quads = []
        span_w = 2 * self.hw - 2 * margin
        cw = (span_w - gap * (cols - 1)) / cols
        slope_len = math.hypot(self.hd, self.ridge - self.wall)
        usable = slope_len - 2 * margin
        rh = (usable - gap * (rows - 1)) / rows
        for r in range(rows):
            s0 = margin + r * (rh + gap)
            s1 = s0 + rh
            for col in range(cols):
                u0 = -self.hw + margin + col * (cw + gap)
                u1 = u0 + cw
                quad = []
                for u, s in ((u0, s0), (u1, s0), (u1, s1), (u0, s1)):
                    frac = s / slope_len
                    ly = -self.hd + frac * self.hd
                    lz = self.wall + frac * (self.ridge - self.wall)
                    quad.append(self._v(u, ly, lz))
                quads.append(quad)
        return quads

    def array_centre(self):
        mid = (self.wall + self.ridge) / 2
        return self._v(0.0, -self.hd / 2, mid)

    def shadow(self, sun):
        se, sn, su = sun
        if su < 0.12:
            return []
        c = self.corners()
        keys = ('front_bl', 'front_br', 'back_br', 'back_bl',
                'ridge_r', 'ridge_l', 'front_tr', 'front_tl')
        pts = []
        for key in keys:
            e, n, z = c[key]
            pts.append((e - se / su * z, n - sn / su * z))
        hull = _convex_hull(pts)
        return [CAM.project(e, n, 0.0) for e, n in hull]


def _convex_hull(points):
    pts = sorted(set((round(x, 5), round(y, 5)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _house_parts(house, sun):
    parts = []
    shadow = house.shadow(sun)
    if len(shadow) >= 3:
        parts.append(f'<path d="{_path(shadow, close=True)}" fill="{SHADOW}" opacity="0.15"/>')

    faces = house.faces()
    ordered = sorted(faces, key=lambda f: min(CAM.depth(*v) for v in f[1]), reverse=True)
    for name, verts, fill in ordered:
        pts = [CAM.project(*v) for v in verts]
        if name == 'roof_front':
            parts.append(f'<path d="{_path(pts, close=True)}" fill="#8f8a82"'
                         f' stroke="{INK}" stroke-width="1" stroke-opacity="0.35"/>')
            for quad in house.module_quads():
                qp = [CAM.project(*v) for v in quad]
                parts.append(f'<path d="{_path(qp, close=True)}" fill="{MODULE}"'
                             f' stroke="{MODULE_EDGE}" stroke-width="0.7"/>')
            continue
        shade = 1.0 if name in ('front', 'roof_back') else 0.92
        parts.append(f'<path d="{_path(pts, close=True)}" fill="{fill}" fill-opacity="{shade}"'
                     f' stroke="{INK}" stroke-width="1" stroke-opacity="0.35"/>')
    return parts


def _tilt_gauge(house):
    c = house.corners()
    base = c['front_bl']
    bx, by = CAM.project(*base)
    rx, ry = CAM.project(*c['ridge_l'])
    hx, hy = CAM.project(base[0], base[1], house.wall)
    parts = [
        f'<line x1="{_fmt(bx)}" y1="{_fmt(by)}" x2="{_fmt(hx)}" y2="{_fmt(hy)}"'
        f' stroke="{MUTED}" stroke-width="0.9" stroke-dasharray="3 3"/>',
        f'<line x1="{_fmt(hx)}" y1="{_fmt(hy)}" x2="{_fmt(rx)}" y2="{_fmt(ry)}"'
        f' stroke="{MUTED}" stroke-width="0.9" stroke-dasharray="3 3"/>',
        _text(hx - 16, hy + 2, f'β {round(house.tilt)}°', 11, MUTED, '600', anchor='end'),
    ]
    return parts


def _legend(x, y, rows):
    parts = [f'<rect x="{x}" y="{y}" width="228" height="{18 + 22 * len(rows)}" rx="8"'
             f' fill="{SURFACE}" stroke="{HAIRLINE}" stroke-width="1"/>']
    for i, (color, dash, label) in enumerate(rows):
        ly = y + 22 + i * 22
        da = f' stroke-dasharray="{dash}"' if dash else ''
        parts.append(f'<line x1="{x + 14}" y1="{ly - 4}" x2="{x + 44}" y2="{ly - 4}"'
                     f' stroke="{color}" stroke-width="2.6" stroke-linecap="round"{da}/>')
        parts.append(_text(x + 54, ly, label, 12, BODY, anchor='start'))
    return parts


def _metrics_band(lat, tilt, azimuth, seasons):
    y0 = H - 76
    parts = [f'<line x1="40" y1="{y0 - 14}" x2="{W - 40}" y2="{y0 - 14}"'
             f' stroke="{HAIRLINE}" stroke-width="1"/>']
    cells = []
    for label, decl, color in seasons:
        noon = sg.elevation(lat, decl, 0)
        rise = sg.sunrise_azimuth(lat, decl)
        hours = sg.day_length_hours(lat, decl)
        cells.append((label, color, [
            ('Elevación mediodía', f'{noon:.1f}°'),
            ('Azimut salida', f'{rise:.0f}°'),
            ('Horas de sol', f'{hours:.1f} h'),
        ]))
    span = (W - 120) / len(cells)
    for i, (label, color, rows) in enumerate(cells):
        x = 60 + i * span
        parts.append(f'<rect x="{_fmt(x - 8)}" y="{y0 - 2}" width="3" height="52" rx="1.5"'
                     f' fill="{color}"/>')
        parts.append(_text(x + 4, y0 + 10, label.upper(), 10, MUTED, '700', anchor='start',
                           spacing='0.08em'))
        for j, (k, v) in enumerate(rows):
            parts.append(_text(x + 4, y0 + 28 + j * 15, k, 10, MUTED, anchor='start'))
            parts.append(_text(x + span - 40, y0 + 28 + j * 15, v, 11, INK, '600', anchor='end'))
    return parts


class SolarPathService:

    @staticmethod
    def generate(lat, tilt=None, azimuth=None, hero_hour=8.5):
        lat = float(lat)
        tilt_deg = 30.0 if tilt is None else float(tilt)
        az_deg = 180.0 if azimuth is None else float(azimuth)

        decl_summer = sg.declination(sg.SOLSTICE_SUMMER_DOY)
        decl_equinox = sg.declination(sg.EQUINOX_DOY)
        decl_winter = sg.declination(sg.SOLSTICE_WINTER_DOY)

        house = _House(tilt_deg, az_deg)
        hero = sg.sun_vector(lat, decl_summer, 15.0 * (hero_hour - 12))
        if hero[2] < 0.2:
            hero = sg.sun_vector(lat, decl_summer, 0.0)

        seasons = [('Verano', decl_summer, SUMMER),
                   ('Equinoccio', decl_equinox, EQUINOX),
                   ('Invierno', decl_winter, WINTER)]

        parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{SURFACE}"/>']
        parts += _ground()
        parts += _meridian()
        parts.append(_track_path(lat, decl_equinox, EQUINOX, 1.6, dash='2 6', opacity=0.9))
        parts.append(_track_path(lat, decl_winter, WINTER, 2.4))
        parts.append(_track_path(lat, decl_summer, SUMMER, 2.4))
        parts += _noon_markers(lat, seasons)
        parts += _hour_marks(lat, decl_summer, SUMMER)
        parts += _hour_marks(lat, decl_winter, WINTER, labels=False)
        parts += _cardinals()
        parts += _drop_line(hero[0], hero[1], hero[2], SUN_EDGE, 0.4)
        parts += _incidence_ray(hero, house)
        parts += _house_parts(house, hero)
        parts += _tilt_gauge(house)
        parts += _sun(*hero)

        parts.append(_text(48, 52, 'Trayectoria solar aparente', 20, INK, '600', anchor='start'))
        subtitle = (f'Latitud {abs(lat):.2f}° {"N" if lat >= 0 else "S"} · '
                    f'campo orientado a {az_deg:.0f}° ({_orientation(az_deg)}) '
                    f'con inclinación {tilt_deg:.0f}°')
        parts.append(_text(48, 74, subtitle, 12.5, MUTED, anchor='start'))

        parts += _legend(W - 268, 40, [
            (SUMMER, None, 'Solsticio de verano'),
            (EQUINOX, '2 6', 'Equinoccios'),
            (WINTER, None, 'Solsticio de invierno'),
        ])

        parts += _metrics_band(lat, tilt_deg, az_deg, seasons)

        body = '\n  '.join(p for p in parts if p)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
                f' viewBox="0 0 {W} {H}" role="img"'
                f' aria-label="Diagrama de trayectoria solar en verano, equinoccio e invierno">'
                f'\n  {body}\n</svg>')

    @staticmethod
    def _orientation(azimuth):
        return _orientation(azimuth)


def _orientation(azimuth):
    a = float(azimuth) % 360
    dirs = [(0, 'Norte'), (45, 'NE'), (90, 'Este'), (135, 'SE'), (180, 'Sur'),
            (225, 'SO'), (270, 'Oeste'), (315, 'NO'), (360, 'Norte')]
    return min(dirs, key=lambda d: abs(d[0] - a))[1]

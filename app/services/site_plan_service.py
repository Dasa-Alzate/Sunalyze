"""Planos de situación y disposición de paneles sobre ortofoto PNOA.

Reconstruye en el servidor, de forma determinista, los planos que el usuario
compone en el paso «Disposición» del wizard: pide la ortofoto oficial (WMS del
IGN, con parcelario de Catastro opcional) y dibuja encima los vectores
(cubierta, exclusiones, retícula de paneles, escala gráfica y norte). El SVG
resultante pasa por el mismo cajetín normativo que los esquemas eléctricos.
"""

import base64
import logging
import math
from xml.sax.saxutils import escape

import requests

from app.extensions import cache

logger = logging.getLogger(__name__)

PNOA_WMS_URL = 'https://www.ign.es/wms-inspire/pnoa-ma'
PNOA_LAYER = 'OI.OrthoimageCoverage'
CATASTRO_WMS_URL = 'https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx'
CATASTRO_LAYER = 'Catastro'
ATTRIBUTION = 'Ortofoto PNOA CC-BY 4.0 © Instituto Geográfico Nacional de España · Parcelario © D.G. Catastro'

WMS_TIMEOUT_SECONDS = 8
CACHE_TTL_SECONDS = 60 * 60 * 24 * 30
_KEY_PREFIX = 'wms:getmap:'

M_PER_DEG_LAT = 110574.0
M_PER_DEG_LNG = 111320.0

LOCATION_HALF_EXTENT_M = 150.0
LAYOUT_MARGIN_M = 4.0
TARGET_PX = 1400

STYLE_ROOF = 'fill="#38bdf8" fill-opacity="0.06" stroke="#38bdf8" stroke-width="3" stroke-dasharray="10 6"'
STYLE_EXCLUSION = 'fill="#ef4444" fill-opacity="0.2" stroke="#ef4444" stroke-width="2" stroke-dasharray="6 4"'
STYLE_PANEL = 'fill="#0f2c52" fill-opacity="0.88" stroke="#e2e8f0" stroke-width="1.2"'


def _converter(origin_lat, origin_lng):
    kx = M_PER_DEG_LNG * math.cos(math.radians(origin_lat))

    def to_local(lat, lng):
        return ((lng - origin_lng) * kx, (lat - origin_lat) * M_PER_DEG_LAT)

    def to_latlng(x, y):
        return (origin_lat + y / M_PER_DEG_LAT, origin_lng + x / kx)

    return to_local, to_latlng


class SitePlanService:

    @staticmethod
    def _fetch_wms(base_url, layer, bbox, width, height, fmt='image/jpeg', transparent=False):
        key = f'{_KEY_PREFIX}{layer}:{":".join(f"{v:.6f}" for v in bbox)}:{width}x{height}'
        hit = cache.get(key)
        if hit is not None:
            return hit
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetMap',
            'LAYERS': layer,
            'STYLES': '',
            'SRS': 'EPSG:4326',
            'BBOX': ','.join(f'{v:.7f}' for v in bbox),
            'WIDTH': str(width),
            'HEIGHT': str(height),
            'FORMAT': fmt,
        }
        if transparent:
            params['TRANSPARENT'] = 'TRUE'
        try:
            resp = requests.get(base_url, params=params, timeout=WMS_TIMEOUT_SECONDS)
            resp.raise_for_status()
            if not resp.headers.get('Content-Type', '').startswith('image/'):
                logger.warning('WMS %s devolvió contenido no imagen: %s', layer, resp.headers.get('Content-Type'))
                return None
            cache.set(key, resp.content, timeout=CACHE_TTL_SECONDS)
            return resp.content
        except requests.RequestException:
            logger.warning('WMS %s no disponible para bbox %s', layer, bbox, exc_info=True)
            return None

    @staticmethod
    def _data_uri(image_bytes, fmt='image/jpeg'):
        return f'data:{fmt};base64,{base64.b64encode(image_bytes).decode("ascii")}'

    @staticmethod
    def _scale_bar(width_px, height_px, m_per_px):
        total_m = width_px * m_per_px
        target = total_m / 5
        length_m = max((c for c in (5, 10, 20, 25, 50, 100, 200, 500) if c <= target), default=5)
        length_px = length_m / m_per_px
        x0 = 24
        y0 = height_px - 26
        return (
            f'<rect x="{x0 - 8}" y="{y0 - 20}" width="{length_px + 16 + 46}" height="34" rx="4" fill="#ffffff" fill-opacity="0.85"/>'
            f'<line x1="{x0}" y1="{y0}" x2="{x0 + length_px}" y2="{y0}" stroke="#131316" stroke-width="3"/>'
            f'<line x1="{x0}" y1="{y0 - 6}" x2="{x0}" y2="{y0 + 6}" stroke="#131316" stroke-width="3"/>'
            f'<line x1="{x0 + length_px}" y1="{y0 - 6}" x2="{x0 + length_px}" y2="{y0 + 6}" stroke="#131316" stroke-width="3"/>'
            f'<text x="{x0 + length_px + 10}" y="{y0 + 5}" font-family="monospace" font-size="15" fill="#131316">{length_m:g} m</text>'
        )

    @staticmethod
    def _north_arrow(width_px):
        cx = width_px - 40
        return (
            f'<circle cx="{cx}" cy="44" r="24" fill="#ffffff" fill-opacity="0.85"/>'
            f'<path d="M {cx} 26 L {cx - 8} 52 L {cx} 45 L {cx + 8} 52 Z" fill="#131316"/>'
            f'<text x="{cx}" y="22" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#131316">N</text>'
        )

    @staticmethod
    def _attribution(width_px, height_px):
        return (
            f'<text x="{width_px - 8}" y="{height_px - 8}" text-anchor="end" font-family="monospace"'
            f' font-size="11" fill="#ffffff" stroke="#131316" stroke-width="0.4" paint-order="stroke">{escape(ATTRIBUTION)}</text>'
        )

    @classmethod
    def location_plan_svg(cls, lat, lng):
        lat = float(lat)
        lng = float(lng)
        to_local, to_latlng = _converter(lat, lng)
        lat_min, lng_min = to_latlng(-LOCATION_HALF_EXTENT_M, -LOCATION_HALF_EXTENT_M)
        lat_max, lng_max = to_latlng(LOCATION_HALF_EXTENT_M, LOCATION_HALF_EXTENT_M)
        bbox = (lng_min, lat_min, lng_max, lat_max)
        size = 1200
        ortho = cls._fetch_wms(PNOA_WMS_URL, PNOA_LAYER, bbox, size, size)
        if ortho is None:
            return None
        parts = [f'<image x="0" y="0" width="{size}" height="{size}" href="{cls._data_uri(ortho)}"/>']
        parcels = cls._fetch_wms(CATASTRO_WMS_URL, CATASTRO_LAYER, bbox, size, size, fmt='PNG', transparent=True)
        if parcels is not None:
            parts.append(
                f'<image x="0" y="0" width="{size}" height="{size}" opacity="0.75" href="{cls._data_uri(parcels, "image/png")}"/>'
            )
        c = size / 2
        parts.append(
            f'<circle cx="{c}" cy="{c}" r="26" fill="none" stroke="#dc2626" stroke-width="4"/>'
            f'<line x1="{c - 44}" y1="{c}" x2="{c - 14}" y2="{c}" stroke="#dc2626" stroke-width="4"/>'
            f'<line x1="{c + 14}" y1="{c}" x2="{c + 44}" y2="{c}" stroke="#dc2626" stroke-width="4"/>'
            f'<line x1="{c}" y1="{c - 44}" x2="{c}" y2="{c - 14}" stroke="#dc2626" stroke-width="4"/>'
            f'<line x1="{c}" y1="{c + 14}" x2="{c}" y2="{c + 44}" stroke="#dc2626" stroke-width="4"/>'
        )
        m_per_px = (2 * LOCATION_HALF_EXTENT_M) / size
        parts.append(cls._scale_bar(size, size, m_per_px))
        parts.append(cls._north_arrow(size))
        parts.append(cls._attribution(size, size))
        body = '\n'.join(parts)
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">{body}</svg>'

    @staticmethod
    def _grid_geometry(layout):
        panel = layout.get('panel') or {}
        w_mm = float(panel.get('w_mm') or 0)
        h_mm = float(panel.get('h_mm') or 0)
        if w_mm <= 0 or h_mm <= 0:
            return None
        orientation = layout.get('orientation') or 'v'
        w = (h_mm if orientation == 'h' else w_mm) / 1000
        length = (w_mm if orientation == 'h' else h_mm) / 1000
        coplanar = bool(layout.get('coplanar'))
        beta = 0.0 if coplanar else float(layout.get('beta') or 0)
        depth = length if coplanar else length * math.cos(math.radians(beta))
        row_gap = layout.get('row_gap_m')
        if row_gap is None:
            if coplanar:
                row_gap = 0.02
            else:
                origin = layout.get('origin') or (40.0, 0.0)
                limit = 61 - min(abs(float(origin[0])), 60)
                row_gap = max(0.02, length * math.sin(math.radians(beta)) / math.tan(math.radians(limit)))
        col_gap = layout.get('col_gap_m')
        if col_gap is None:
            col_gap = 0.02
        pitch_x = w + float(col_gap)
        pitch_y = depth + float(row_gap)
        phi = math.radians(float(layout.get('azimut') if layout.get('azimut') is not None else 180))
        d = (math.sin(phi), math.cos(phi))
        r = (-d[1], d[0])

        def cell_corners(i, j):
            cx = i * pitch_x * r[0] + j * pitch_y * d[0]
            cy = i * pitch_x * r[1] + j * pitch_y * d[1]
            hw = w / 2
            hd = depth / 2
            return [
                (cx - hw * r[0] - hd * d[0], cy - hw * r[1] - hd * d[1]),
                (cx + hw * r[0] - hd * d[0], cy + hw * r[1] - hd * d[1]),
                (cx + hw * r[0] + hd * d[0], cy + hw * r[1] + hd * d[1]),
                (cx - hw * r[0] + hd * d[0], cy - hw * r[1] + hd * d[1]),
            ]

        return cell_corners

    @classmethod
    def layout_plan_svg(cls, layout):
        origin = layout.get('origin')
        roof = layout.get('roof') or []
        cells = layout.get('cells') or []
        if not origin or len(roof) < 3 or not cells:
            return None
        cell_corners = cls._grid_geometry(layout)
        if cell_corners is None:
            return None

        to_local, to_latlng = _converter(float(origin[0]), float(origin[1]))
        roof_local = [to_local(float(p[0]), float(p[1])) for p in roof]
        exclusions_local = [
            [to_local(float(p[0]), float(p[1])) for p in poly]
            for poly in (layout.get('exclusions') or [])
        ]
        panels_local = [cell_corners(int(i), int(j)) for i, j in cells]

        xs = [p[0] for p in roof_local] + [c[0] for corners in panels_local for c in corners]
        ys = [p[1] for p in roof_local] + [c[1] for corners in panels_local for c in corners]
        x_min = min(xs) - LAYOUT_MARGIN_M
        x_max = max(xs) + LAYOUT_MARGIN_M
        y_min = min(ys) - LAYOUT_MARGIN_M
        y_max = max(ys) + LAYOUT_MARGIN_M
        w_m = x_max - x_min
        h_m = y_max - y_min
        scale = TARGET_PX / max(w_m, h_m)
        width_px = max(1, round(w_m * scale))
        height_px = max(1, round(h_m * scale))

        def px(point):
            return ((point[0] - x_min) * scale, (y_max - point[1]) * scale)

        def points_attr(poly):
            return ' '.join(f'{x:.1f},{y:.1f}' for x, y in (px(p) for p in poly))

        lat_min, lng_min = to_latlng(x_min, y_min)
        lat_max, lng_max = to_latlng(x_max, y_max)
        bbox = (lng_min, lat_min, lng_max, lat_max)

        parts = []
        ortho = cls._fetch_wms(PNOA_WMS_URL, PNOA_LAYER, bbox, width_px, height_px)
        if ortho is not None:
            parts.append(f'<image x="0" y="0" width="{width_px}" height="{height_px}" href="{cls._data_uri(ortho)}"/>')
        else:
            parts.append(f'<rect x="0" y="0" width="{width_px}" height="{height_px}" fill="#e5e7eb"/>')
            parts.append(
                f'<text x="{width_px / 2}" y="24" text-anchor="middle" font-family="monospace" font-size="14"'
                f' fill="#666666">Ortofoto no disponible — plano esquemático</text>'
            )

        parts.append(f'<polygon points="{points_attr(roof_local)}" {STYLE_ROOF}/>')
        for poly in exclusions_local:
            parts.append(f'<polygon points="{points_attr(poly)}" {STYLE_EXCLUSION}/>')
        for corners in panels_local:
            parts.append(f'<polygon points="{points_attr(corners)}" {STYLE_PANEL}/>')

        parts.append(cls._scale_bar(width_px, height_px, 1 / scale))
        parts.append(cls._north_arrow(width_px))
        parts.append(cls._attribution(width_px, height_px))
        body = '\n'.join(parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}"'
            f' viewBox="0 0 {width_px} {height_px}">{body}</svg>'
        )

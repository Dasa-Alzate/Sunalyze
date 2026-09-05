
import csv
import io
import logging
import re

from . import http
from .base import NormalizedProduct
from .scraper import BrandScraper

logger = logging.getLogger(__name__)

CSV_URL = ('https://raw.githubusercontent.com/NREL/SAM/develop/'
           'deploy/libraries/CEC%20Inverters.csv')

ALLOWED = {
    'fronius': 'Fronius',
    'sma america': 'SMA',
    'huawei': 'Huawei',
    'sungrow': 'Sungrow',
    'growatt': 'Growatt',
    'goodwe': 'GoodWe',
    'ginlong': 'Solis',
    'solaredge': 'SolarEdge',
    'solax': 'SolaX',
    'foxess': 'FoxESS',
    'enphase': 'Enphase',
    'ingeteam': 'Ingeteam',
    'hoymiles': 'Hoymiles',
    'delta electronics': 'Delta',
    'power electronics': 'Power Electronics',
    'abb': 'ABB',
}

_COLUMNS = ('Name', 'Vac', 'Paco', 'Pdco', 'Vdcmax', 'Idcmax', 'Mppt_low', 'Mppt_high')

_VAC_PREFERENCE = (240.0, 230.0, 220.0, 208.0, 480.0, 277.0)

_NAME = re.compile(r'^(?P<mfr>[^:]+):\s*(?P<model>.+?)\s*(?:\{[^}]*\})?\s*$')


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _brand_for(manufacturer):
    low = (manufacturer or '').lower()
    for needle, display in ALLOWED.items():
        if needle in low:
            return display
    return None


def _vac_rank(vac):
    try:
        return _VAC_PREFERENCE.index(float(vac))
    except (TypeError, ValueError):
        return len(_VAC_PREFERENCE)


class CECInverterScraper(BrandScraper):
    brand = 'CEC'
    kind = 'inverter'
    requires_product_brand = True

    def __init__(self):
        self._csv_entry = None

    def discover(self):
        fetched = http.conditional_get(CSV_URL, force=self._force)
        if fetched is None:
            logger.info('CEC inversores: el CSV no ha cambiado desde la última ejecución')
            return []
        self._csv_entry = fetched

        rows = csv.reader(io.StringIO(fetched.text))
        header = next(rows, [])
        idx = {c: i for i, c in enumerate(header)}
        missing = [c for c in _COLUMNS if c not in idx]
        if missing:
            raise ValueError(f'CEC inversores: columnas ausentes en el CSV: {missing}')

        best = {}
        for r in rows:
            if len(r) <= idx['Mppt_high']:
                continue
            match = _NAME.match(r[idx['Name']])
            if not match:
                continue
            manufacturer = match.group('mfr').strip()
            model = match.group('model').strip()
            display = _brand_for(manufacturer)
            if not display or not model:
                continue
            if _f(r[idx['Paco']]) is None or _f(r[idx['Vdcmax']]) is None:
                continue
            if model.lower().startswith(display.lower()):
                model = model[len(display):].strip()
            nombre = f'{display} {model}' if model else display
            rank = _vac_rank(r[idx['Vac']])
            kept = best.get(nombre)
            if kept and kept[0] <= rank:
                continue
            best[nombre] = (rank, {
                'external_id': ('cec-inv/' + nombre)[:120],
                'url': CSV_URL,
                'kind': self.kind,
                'brand': display,
                'nombre': nombre,
                '_row': {c: r[idx[c]] for c in _COLUMNS},
            })

        refs = [ref for _, ref in best.values()]
        logger.info('CEC inversores: %s modelos tras filtrar por marca y deduplicar por Vac',
                    len(refs))
        return refs

    def fetch(self, ref, force=False):
        return ref.pop('_row', None)

    def remember(self, ref):
        http.remember(self._csv_entry)
        self._csv_entry = None

    def parse(self, ref, row):
        paco = _f(row['Paco'])
        pdco = _f(row['Pdco'])

        fields = {
            'nombre': ref['nombre'][:100],
            'power': round(paco / 1000, 3) if paco else None,
            'vmax': _f(row['Vdcmax']),
            'mppt_v_min': _f(row['Mppt_low']),
            'mppt_v_max': _f(row['Mppt_high']),
            'I_max_input': _f(row['Idcmax']),
        }
        if paco and pdco:
            fields['y'] = round(paco / pdco * 100, 2)

        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=self.kind, external_id=ref['external_id'],
                                  source_url=CSV_URL, fields=fields,
                                  brand=ref['brand'])]

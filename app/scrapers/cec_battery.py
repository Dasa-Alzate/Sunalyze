
import io
import logging
import re

import openpyxl

from . import http
from .base import NormalizedProduct, to_float_eu
from .scraper import BrandScraper

logger = logging.getLogger(__name__)

XLSX_URL = 'https://solarequipment.energy.ca.gov/Home/DownloadtoExcel?filename=BatteryList'

ALLOWED = {
    'pylon technologies': 'Pylontech',
    'ningbo deye ess technology': 'Deye',
    'shenzhen growatt new energy': 'Growatt',
    'dyness digital energy technology': 'Dyness',
    'byd auto industry company': 'BYD',
    'shenzhen byd electronics': 'BYD',
    'shenzhen byd lithium battery': 'BYD',
    'goodwe technologies': 'GoodWe',
    'lg energy solution': 'LG Energy Solution',
    'solax power network technology': 'SolaX',
    'foxess': 'FoxESS',
    'ecoflow': 'EcoFlow',
    'alpha ess': 'Alpha ESS',
    'tesla': 'Tesla',
    'huawei': 'Huawei',
    'enphase': 'Enphase',
    'sonnen': 'sonnen',
    'sungrow': 'Sungrow',
    'victron': 'Victron Energy',
}

_HEADER_ROW = 11
_COL = {'manufacturer': 0, 'brand': 1, 'model': 2, 'technology': 3,
        'description': 4, 'capacity_kwh': 8, 'power_kw': 9, 'efficiency': 10}

_NO_INFO = re.compile(r'no information', re.IGNORECASE)


def _brand_for(manufacturer):
    low = (manufacturer or '').lower()
    for needle, display in ALLOWED.items():
        if needle in low:
            return display
    return None


def _num(value):
    if value is None or _NO_INFO.search(str(value)):
        return None
    m = re.search(r'[0-9][0-9.,]*', str(value))
    return to_float_eu(m.group(0)) if m else None


def _voltage_from(*texts):
    for text in texts:
        m = re.search(r'\b(\d{2,4})\s*V(?:dc|DC)?\b', str(text or ''))
        if m:
            value = float(m.group(1))
            if 12 <= value <= 2000:
                return value
    return None


class CECBatteryScraper(BrandScraper):
    brand = 'CEC'
    kind = 'battery'
    requires_product_brand = True

    def __init__(self):
        self._xlsx_entry = None

    def discover(self):
        fetched = http.conditional_get(XLSX_URL, force=self._force, binary=True)
        if fetched is None:
            logger.info('CEC baterías: el Excel no ha cambiado desde la última ejecución')
            return []
        self._xlsx_entry = fetched

        workbook = openpyxl.load_workbook(io.BytesIO(fetched.text), read_only=True)
        sheet = workbook.active
        refs, seen = [], set()
        for row in sheet.iter_rows(min_row=_HEADER_ROW + 2, values_only=True):
            manufacturer = str(row[_COL['manufacturer']] or '').strip()
            model = str(row[_COL['model']] or '').strip()
            display = _brand_for(manufacturer)
            if not display or not model:
                continue
            key = f'{display} {model}'
            if key in seen:
                continue
            seen.add(key)
            refs.append({'external_id': ('cec-bat/' + key)[:120], 'url': XLSX_URL,
                         'kind': self.kind, 'brand': display,
                         '_row': {name: row[col] for name, col in _COL.items()}})
        workbook.close()
        logger.info('CEC baterías: %s modelos tras filtrar por marca', len(refs))
        return refs

    def fetch(self, ref, force=False):
        return ref.pop('_row', None)

    def remember(self, ref):
        http.remember(self._xlsx_entry)
        self._xlsx_entry = None

    def parse(self, ref, row):
        model = str(row['model'] or '').strip()
        voltage = _voltage_from(model, row['description'])
        notes = []
        if voltage is None:
            notes.append('la lista CEC no publica el voltaje nominal; verificar en el '
                         'datasheet del fabricante antes de dimensionar')

        fields = {
            'nombre': f'{ref["brand"]} {model}'[:100],
            'capacity_kwh': _num(row['capacity_kwh']),
            'power_kw': _num(row['power_kw']),
            'voltage': voltage,
            'technology': str(row['technology'] or '').strip()[:50] or None,
            'round_trip_efficiency': _num(row['efficiency']),
        }
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=self.kind, external_id=ref['external_id'],
                                  source_url=XLSX_URL, fields=fields,
                                  brand=ref['brand'], notes=notes)]

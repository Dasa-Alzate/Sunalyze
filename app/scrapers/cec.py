
import csv
import io
import logging

from . import http
from .base import NormalizedProduct
from .brands import KNOWN_BRANDS, normalize_brand
from .scraper import BrandScraper

logger = logging.getLogger(__name__)

CSV_URL = ('https://raw.githubusercontent.com/NREL/SAM/develop/'
           'deploy/libraries/CEC%20Modules.csv')
MIN_STC_W = 350.0

ALLOWED_BRANDS = {
    'JA Solar', 'LONGi', 'Trina Solar', 'Jinko Solar', 'Canadian Solar', 'Risen',
    'Qcells', 'REC', 'Maxeon', 'SunPower', 'Phono Solar', 'ZNShine', 'Suntech',
    'DMEGC', 'Leapton', 'Peimar', 'Exiom', 'Hyundai', 'Seraphim', 'Yingli', 'Sharp',
}

_COLUMNS = ('Name', 'Manufacturer', 'STC', 'V_oc_ref', 'V_mp_ref', 'I_mp_ref',
            'I_sc_ref', 'Length', 'Width', 'A_c', 'beta_oc', 'gamma_pmp',
            'T_NOCT', 'Technology', 'Bifacial')


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class CECScraper(BrandScraper):
    brand = 'CEC'
    kind = 'panel'
    requires_product_brand = True

    def __init__(self):
        self._csv_entry = None

    def discover(self):
        fetched = http.conditional_get(CSV_URL, force=self._force)
        if fetched is None:
            logger.info('CEC: el CSV no ha cambiado desde la última ejecución')
            return []
        self._csv_entry = fetched

        rows = csv.reader(io.StringIO(fetched.text))
        header = next(rows, [])
        idx = {c: i for i, c in enumerate(header)}
        missing = [c for c in _COLUMNS if c not in idx]
        if missing:
            raise ValueError(f'CEC: columnas ausentes en el CSV: {missing}')

        refs, seen = [], set()
        for r in rows:
            if len(r) <= idx['T_NOCT']:
                continue
            display = KNOWN_BRANDS.get(normalize_brand(r[idx['Manufacturer']]))
            if display not in ALLOWED_BRANDS:
                continue
            stc = _f(r[idx['STC']])
            if stc is None or stc < MIN_STC_W:
                continue
            name = r[idx['Name']].strip()
            if not name or name in seen:
                continue
            seen.add(name)
            refs.append({'external_id': ('cec/' + name)[:120], 'url': CSV_URL,
                         'kind': self.kind, 'brand': display,
                         '_row': {c: r[idx[c]] for c in _COLUMNS}})
        logger.info('CEC: %s módulos tras filtrar por marca y STC>=%sW',
                    len(refs), int(MIN_STC_W))
        return refs

    def fetch(self, ref, force=False):
        return ref.pop('_row', None)

    def remember(self, ref):
        http.remember(self._csv_entry)
        self._csv_entry = None

    @staticmethod
    def _display_name(raw_name, manufacturer, display):
        name = raw_name.strip()
        if name.lower().startswith(manufacturer.strip().lower()):
            name = name[len(manufacturer.strip()):].strip()
        return f'{display} {name}' if name else display

    def parse(self, ref, row):
        voc = _f(row['V_oc_ref'])
        stc = _f(row['STC'])
        area = _f(row['A_c'])
        beta_oc = _f(row['beta_oc'])
        length_m = _f(row['Length'])
        width_m = _f(row['Width'])

        fields = {
            'nombre': self._display_name(row['Name'], row['Manufacturer'],
                                         ref['brand'])[:100],
            'power': stc,
            'voc': voc,
            'vmp': _f(row['V_mp_ref']),
            'imp': _f(row['I_mp_ref']),
            'isc': _f(row['I_sc_ref']),
            'tcp': _f(row['gamma_pmp']),
            't_noct': _f(row['T_NOCT']),
        }
        if beta_oc is not None and voc:
            fields['tcv'] = round(beta_oc / voc * 100, 4)
        if stc and area:
            fields['y'] = round(stc / area / 10, 2)
        if length_m:
            fields['height'] = int(round(length_m * 1000))
        if width_m:
            fields['width'] = int(round(width_m * 1000))

        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=self.kind, external_id=ref['external_id'],
                                  source_url=CSV_URL, fields=fields,
                                  brand=ref['brand'])]

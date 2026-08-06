
import logging
import re
import urllib.parse

import lxml.html

from . import sitemap
from .base import NormalizedProduct, grab, grab_range, to_float_eu
from .scraper import BrandScraper

logger = logging.getLogger(__name__)

SITEMAP_INDEX = 'https://www.fronius.com/sitemap-index.xml'
COUNTRY = 'spain'
CATALOG_SEGMENT = '/todos-los-productos/'
INVERTER_SEGMENT = 'inversor'

VMAX_RANGE = ['Rango de tensión de entrada CC', 'Rango de tensión CC de entrada']
VMAX_MPP = ['Tensión MPP máxima', 'Máx. Tensión MPP', 'Tensión MPP max']
POWER_KW = ['Potencia nominal CA', 'Potencia nominal de salida CA']
POWER_MAX_KVA = ['Máxima potencia de salida', 'Máx. potencia de salida']
EFFICIENCY = ['Máximo rendimiento', 'Eficiencia Máxima', 'Grado de rendimiento máximo']
I_INPUT = ['Máxima corriente de entrada', 'Corriente máxima de entrada',
           'Máx. corriente de entrada de la serie fotovoltaica']
I_OUTPUT = ['Corriente de salida de CA máxima', 'Corriente de salida CA (Ica nom)',
            'Máxima corriente de salida CA', 'Corriente máxima de salida']
MPP_RANGE = ['Rango de tensión MPP', 'Rango de tensión Umpp', 'Rango Umpp']
MPPT_COUNT = ['Número de seguidores MPP', 'Número de MPPT', 'Cantidad de seguidores MPP',
              'Número de seguidores del punto de máxima potencia']
ISC_MAX = ['Máxima corriente de cortocircuito', 'Corriente máxima de cortocircuito',
           'Máx. corriente de cortocircuito']


def _tail(url):
    decoded = urllib.parse.unquote(url)
    if CATALOG_SEGMENT not in decoded:
        return []
    return [s for s in decoded.split(CATALOG_SEGMENT)[-1].split('/') if s]


def _is_inverter_model(url):
    parts = _tail(url)
    return len(parts) == 3 and parts[0] == INVERTER_SEGMENT


def _title(doc, fallback):
    for xpath in ('//meta[@property="og:title"]/@content', '//title/text()'):
        found = doc.xpath(xpath)
        if found and found[0].strip():
            return found[0].strip()
    headings = doc.xpath('//h1')
    return headings[0].text_content().strip() if headings else fallback


def _power_from_title(title):
    cleaned = re.sub(r'GEN\s*\d+', ' ', title or '', flags=re.IGNORECASE)
    m = re.search(r'(\d+(?:[.,]\d+)?)', cleaned)
    return to_float_eu(m.group(1)) if m else None


def _kilo(text, labels):
    value = grab(text, labels, 'kW')
    if value is not None:
        return value
    value = grab(text, labels, 'W')
    return value / 1000 if value is not None else None


def _kilo_va(text, labels):
    value = grab(text, labels, 'kVA')
    if value is not None:
        return value
    value = grab(text, labels, 'VA')
    return value / 1000 if value is not None else None


class FroniusScraper(BrandScraper):
    brand = 'Fronius'
    kind = 'inverter'

    def discover(self):
        urls = sitemap.discover_urls(
            SITEMAP_INDEX,
            keep=_is_inverter_model,
            follow=lambda u: f'country={COUNTRY}' in u,
        )
        refs = [{'external_id': '/'.join(_tail(u)[1:])[:120], 'url': u, 'kind': self.kind}
                for u in urls]
        logger.info('Fronius: %s fichas de inversor descubiertas', len(refs))
        return refs

    def parse(self, ref, raw):
        doc = lxml.html.fromstring(raw)
        title = _title(doc, ref['external_id'])
        text = ' '.join(doc.text_content().split())
        notes = []

        _, vmax = grab_range(text, VMAX_RANGE, 'V')
        mppt_v_min, mppt_v_max = grab_range(text, MPP_RANGE, 'V')
        if mppt_v_max is None:
            mppt_v_max = grab(text, VMAX_MPP, 'V')
        if vmax is None:
            vmax = mppt_v_max
            if vmax is not None:
                notes.append('vmax tomado de la tensión MPP máxima: la ficha no publica '
                             'Ucc máx., el valor es conservador')

        mppt_count = grab(text, MPPT_COUNT, '')
        if mppt_count is not None:
            mppt_count = int(mppt_count) if 1 <= mppt_count <= 50 else None

        power = _kilo(text, POWER_KW)
        if power is None:
            power = _power_from_title(title)
            if power is not None:
                notes.append('power deducido del nombre del modelo: la ficha no publica '
                             'potencia nominal CA')

        fields = {
            'nombre': title,
            'power': power,
            'power_max': _kilo_va(text, POWER_MAX_KVA),
            'vmax': vmax,
            'y': grab(text, EFFICIENCY, '%'),
            'I_max_input': grab(text, I_INPUT, 'A'),
            'I_max_output': grab(text, I_OUTPUT, 'A'),
            'mppt_v_min': mppt_v_min,
            'mppt_v_max': mppt_v_max,
            'mppt_count': mppt_count,
            'isc_max_per_mppt': grab(text, ISC_MAX, 'A'),
        }
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=self.kind, external_id=ref['external_id'],
                                  source_url=ref['url'], fields=fields, notes=notes)]

"""Adapter de Autosolar (distribuidor multi-marca).

Autosolar vende equipos de muchos fabricantes; cada ficha declara la marca (atributo
estructurado) y una tabla de especificaciones. La identidad y la marca salen de la
página; el servicio enruta cada producto al catálogo de su marca. Sin marca deducida,
el producto no entra (requires_product_brand).
"""

import logging
import re

import lxml.html
import requests

from .base import NormalizedProduct, to_float_eu, power_from_name
from .brands import deduce_brand

logger = logging.getLogger(__name__)

_UA = 'SunalyzeBot/0.1 (+catalog-sync; contact: ops@sunalyze.es)'

SEED = [
    {'kind': 'inverter', 'url': 'https://autosolar.es/inversores'},
    {'kind': 'panel', 'url': 'https://autosolar.es/placas-solares'},
]


def _cell(doc, labels, unit):
    for row in doc.xpath('//table[contains(@class, "data-sheet")]//tr'):
        cells = row.xpath('.//td')
        if len(cells) < 2:
            continue
        label = cells[0].text_content().lower()
        if any(l.lower() in label for l in labels):
            m = re.search(r'([0-9][0-9.,]*)\s*' + unit, cells[1].text_content())
            if m:
                return to_float_eu(m.group(1))
    return None


class AutoSolarScraper:
    brand = 'AutoSolar'
    requires_product_brand = True

    def discover(self):
        return []

    def fetch(self, ref):
        resp = requests.get(ref['url'], headers={'User-Agent': _UA}, timeout=20)
        resp.raise_for_status()
        return resp.text

    def parse(self, ref, raw):
        doc = lxml.html.fromstring(raw)
        titles = doc.xpath('//h1[contains(@class, "product-name")]') or doc.xpath('//h1')
        title = titles[0].text_content().strip() if titles else ''
        attrs = doc.xpath('//*[@itemprop="brand"]/@content')
        attr = attrs[0] if attrs else None
        display, _ = deduce_brand(attr, title)

        kind = ref['kind']
        if kind == 'inverter':
            fields = {
                'nombre': title,
                'power': _cell(doc, ['potencia nominal', 'potencia de salida'], r'kW') or power_from_name(title),
                'vmax': _cell(doc, ['tensión máxima de entrada', 'tension maxima de entrada'], r'V'),
                'y': _cell(doc, ['rendimiento máximo', 'rendimiento maximo', 'eficiencia'], r'%'),
            }
        else:
            fields = {
                'nombre': title,
                'power': _cell(doc, ['potencia'], r'W'),
                'voc': _cell(doc, ['circuito abierto', 'voc'], r'V'),
                'vmp': _cell(doc, ['máxima potencia', 'maxima potencia', 'vmp'], r'V'),
                'imp': _cell(doc, ['corriente de máxima', 'corriente de maxima', 'imp'], r'A'),
            }
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=kind, external_id=ref['external_id'],
                                  source_url=ref['url'], fields=fields, brand=display)]

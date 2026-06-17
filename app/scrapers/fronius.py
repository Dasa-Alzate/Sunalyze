"""Adapter de Fronius: HTML técnico oficial (estático, sin JS).

Verificado: las páginas technical-data exponen las specs como texto etiquetado
(Max. input voltage, MPP range, Max. continuous output current, Max. efficiency).
La identidad (modelo + potencia AC) viene del seed de descubrimiento; la página
enriquece vmax, eficiencia y corrientes. Lo que no aparezca queda nulo.
"""

import logging
import lxml.html
import requests

from .base import NormalizedProduct, grab, power_from_name

logger = logging.getLogger(__name__)

_UA = 'SunalyzeBot/0.1 (+catalog-sync; contact: ops@sunalyze.es)'
_BASE = 'https://www.fronius.com/en-us/usa/solar-energy/installers-partners/technical-data/all-products/inverters/fronius-primo-ul/'

SEED = [
    {'slug': 'fronius-primo-5-0-1-208-240', 'nombre': 'Fronius Primo 5.0-1'},
    {'slug': 'fronius-primo-10-0-1-208-240', 'nombre': 'Fronius Primo 10.0-1'},
    {'slug': 'fronius-primo-15-0-1-208-240', 'nombre': 'Fronius Primo 15.0-1'},
]


class FroniusScraper:
    brand = 'Fronius'
    kind = 'inverter'

    def discover(self):
        return [{'external_id': s['slug'], 'nombre': s['nombre'], 'url': _BASE + s['slug']} for s in SEED]

    def fetch(self, ref):
        resp = requests.get(ref['url'], headers={'User-Agent': _UA}, timeout=20)
        resp.raise_for_status()
        return lxml.html.fromstring(resp.text).text_content()

    def parse(self, ref, text):
        fields = {
            'nombre': ref['nombre'],
            'power': power_from_name(ref['nombre']),
            'vmax': grab(text, ['Max. input voltage', 'Max input voltage'], r'V\b'),
            'y': grab(text, ['Max. efficiency', 'Maximum efficiency'], r'%'),
            'I_max_input': grab(text, ['Max. usable input current', 'Max usable input current'], r'A\b'),
            'I_max_output': grab(text, ['Max. continuous output current', 'Max. output current'], r'A\b'),
        }
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=self.kind, external_id=ref['external_id'],
                                  source_url=ref['url'], fields=fields)]

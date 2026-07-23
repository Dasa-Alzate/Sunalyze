"""Adapter de Autosolar (distribuidor multi-marca).

Autosolar vende equipos de muchos fabricantes; cada ficha declara la marca en un
enlace de fabricante y las especificaciones en una lista `ul.specification` con pares
«Etiqueta: valor». La identidad y la marca salen de la página; el servicio enruta cada
producto al catálogo de su marca. Sin marca deducida, el producto no entra
(requires_product_brand).

Cobertura realista: los paneles exponen los vitales (potencia, Voc, Vmp, Imp) en la
ficha. Los inversores a menudo no listan la tensión máxima de entrada DC (`vmax`); esos
quedan parciales y se descartan por las reglas vitales.
"""

import logging
import re
import time
import unicodedata

import lxml.html
import requests

from .base import NormalizedProduct, to_float_eu, power_from_name
from .brands import deduce_brand

logger = logging.getLogger(__name__)

_UA = 'SunalyzeBot/0.1 (+catalog-sync; contact: ops@sunalyze.es)'
_BASE = 'https://autosolar.es'
_PAUSE = 0.3
_MAX_PAGES = 40

SEED = [
    {'kind': 'panel', 'url': _BASE + '/paneles-solares'},
    {'kind': 'inverter', 'url': _BASE + '/inversores'},
    {'kind': 'wire', 'url': _BASE + '/cables'},
]


def _strip(text):
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()


def _num(value):
    m = re.search(r'[0-9][0-9.,]*', value or '')
    return to_float_eu(m.group(0)) if m else None


def _watts_from_title(title):
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*W\b', title or '', re.IGNORECASE)
    return to_float_eu(m.group(1)) if m else None


def _spec_pairs(doc):
    pairs = {}
    datasheet = None
    for li in doc.xpath('//ul[contains(@class, "specification")]/li'):
        raw = li.text_content()
        if ':' not in raw:
            continue
        label, _, value = raw.partition(':')
        key = ' '.join(_strip(label).split())
        link = li.xpath('.//a/@href')
        if 'ficha' in key and link:
            datasheet = link[0]
        pairs[key] = ' '.join(value.split())
    return pairs, datasheet


def _find(pairs, *needles):
    for key, value in pairs.items():
        if all(n in key for n in needles):
            return value
    return None


def _seccion_from_title(title):
    """Captura la seccion en mm2 de un titulo tipo «Cable 6mm2» o «Cable 4 mm²»."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*mm', title or '', re.IGNORECASE)
    return to_float_eu(m.group(1)) if m else None


def _wire_material(*texts):
    """Deduce el material conductor a partir del texto de la ficha.

    'aluminio'/'al' → 'Al'; en cualquier otro caso 'Cu' (cobre, valor por defecto).
    """
    blob = _strip(' '.join(t for t in texts if t))
    if 'alumin' in blob or re.search(r'\bal\b', blob):
        return 'Al'
    return 'Cu'


def _wire_type(title):
    """Extrae la designacion corta del cable del titulo (p. ej. 'H1Z2Z2-K').

    Devuelve el codigo normalizado (mayusculas, ≤10 caracteres) o 'PV' por defecto.
    """
    m = re.search(r'\b([A-Z0-9]*[A-Z][A-Z0-9]*-[A-Z])\b', (title or '').upper())
    if m:
        return m.group(1)[:10]
    if re.search(r'\bPV\b', (title or '').upper()):
        return 'PV'
    return 'PV'


class AutoSolarScraper:
    brand = 'AutoSolar'
    requires_product_brand = True
    max_products = 60

    def discover(self):
        refs = []
        for seed in SEED:
            url = seed['url']
            pages = 0
            while url and pages < _MAX_PAGES:
                try:
                    resp = requests.get(url, headers={'User-Agent': _UA}, timeout=20)
                    resp.raise_for_status()
                except Exception:
                    logger.exception('Fallo al listar %s', url)
                    break
                doc = lxml.html.fromstring(resp.text)
                doc.make_links_absolute(_BASE)
                anchors = doc.xpath('//a[.//div[contains(@class, "product-frame")]]')
                for a in anchors:
                    href = a.get('href')
                    if not href:
                        continue
                    refs.append({'external_id': href.split('autosolar.es/')[-1],
                                 'url': href, 'kind': seed['kind'],
                                 'nombre': (a.get('title') or '').strip()})
                    if self.max_products and len(refs) >= self.max_products:
                        return refs
                nxt = doc.xpath('//link[@rel="next"]/@href') or doc.xpath('//a[@rel="next"]/@href')
                url = nxt[0] if nxt else None
                pages += 1
                time.sleep(_PAUSE)
        return refs

    def fetch(self, ref):
        resp = requests.get(ref['url'], headers={'User-Agent': _UA}, timeout=20)
        resp.raise_for_status()
        time.sleep(_PAUSE)
        return resp.text

    def parse(self, ref, raw):
        doc = lxml.html.fromstring(raw)
        titles = doc.xpath('//h1[contains(@class, "title")]') or doc.xpath('//h1')
        title = titles[0].text_content().strip() if titles else (ref.get('nombre') or '')
        attrs = doc.xpath('//a[contains(@href, "fabricante")]/@title')
        display, _ = deduce_brand(attrs[0] if attrs else None, title)

        pairs, datasheet = _spec_pairs(doc)
        kind = ref['kind']
        if kind == 'wire':
            material_txt = _find(pairs, 'material') or _find(pairs, 'conductor')
            conductores = _num(_find(pairs, 'conductores') or _find(pairs, 'numero', 'polos'))
            fields = {
                'nombre': title,
                'seccion': _seccion_from_title(title) or _num(_find(pairs, 'seccion')),
                'corriente': _num(_find(pairs, 'intensidad', 'admisible')
                                  or _find(pairs, 'corriente') or _find(pairs, 'intensidad')),
                'material': _wire_material(title, material_txt),
                'no_conductores': int(conductores) if conductores else 1,
                'tipo': _wire_type(title),
            }
            fields = {k: v for k, v in fields.items() if v is not None}
            return [NormalizedProduct(kind=kind, external_id=ref['external_id'],
                                      source_url=ref['url'], fields=fields,
                                      brand=display or self.brand)]
        if kind == 'inverter':
            fields = {
                'nombre': title,
                'power': power_from_name(title) or _num(_find(pairs, 'potencia', 'salida')),
                'vmax': _num(_find(pairs, 'tension', 'maxima', 'entrada')
                             or _find(pairs, 'voltaje', 'maximo', 'entrada')),
                'y': _num(_find(pairs, 'eficiencia') or _find(pairs, 'rendimiento')),
            }
        else:
            fields = {
                'nombre': title,
                'power': _watts_from_title(title) or _num(_find(pairs, 'rango', 'potencia')),
                'voc': _num(_find(pairs, 'tension', 'circuito', 'abierto')),
                'vmp': _num(_find(pairs, 'tension', 'maxima', 'potencia')),
                'imp': _num(_find(pairs, 'corriente', 'maxima', 'potencia')),
                'isc': _num(_find(pairs, 'corriente', 'cortocircuito')),
                'y': _num(_find(pairs, 'eficiencia')),
            }
        if datasheet:
            fields['datasheet'] = datasheet
        fields = {k: v for k, v in fields.items() if v is not None}
        return [NormalizedProduct(kind=kind, external_id=ref['external_id'],
                                  source_url=ref['url'], fields=fields, brand=display)]


import logging
import re
import unicodedata

import lxml.html

from .base import NormalizedProduct, to_float_eu
from .brands import deduce_brand
from .http import plain_get
from .scraper import BrandScraper

logger = logging.getLogger(__name__)

_BASE = 'https://autosolar.es'
_MAX_PAGES = 200

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


def _watts(value):
    m = re.search(r'[0-9][0-9.,]*', value or '')
    if not m:
        return None
    raw = m.group(0)
    if re.fullmatch(r'\d{1,3}(\.\d{3})+', raw):
        raw = raw.replace('.', '')
    return to_float_eu(raw)


def _kw(value):
    watts = _watts(value)
    return round(watts / 1000, 3) if watts is not None else None


def _range_max(value):
    numbers = [to_float_eu(n) for n in re.findall(r'[0-9][0-9.,]*', value or '')]
    numbers = [n for n in numbers if n is not None]
    return max(numbers) if numbers else None


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
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*mm', title or '', re.IGNORECASE)
    return to_float_eu(m.group(1)) if m else None


def _wire_material(*texts):
    blob = _strip(' '.join(t for t in texts if t))
    if 'alumin' in blob or re.search(r'\bal\b', blob):
        return 'Al'
    return 'Cu'


def _wire_type(title):
    m = re.search(r'\b([A-Z0-9]*[A-Z][A-Z0-9]*-[A-Z])\b', (title or '').upper())
    if m:
        return m.group(1)[:10]
    if re.search(r'\bPV\b', (title or '').upper()):
        return 'PV'
    return 'PV'


class AutoSolarScraper(BrandScraper):
    brand = 'AutoSolar'
    requires_product_brand = True

    def discover(self):
        refs = []
        seen = set()
        for seed in SEED:
            url = seed['url']
            pages = 0
            while url and pages < _MAX_PAGES:
                try:
                    raw = plain_get(url)
                except Exception:
                    logger.exception('Fallo al listar %s', url)
                    break
                doc = lxml.html.fromstring(raw)
                doc.make_links_absolute(_BASE)
                for a in doc.xpath('//a[.//div[contains(@class, "product-frame")]]'):
                    href = a.get('href')
                    if not href or href in seen:
                        continue
                    seen.add(href)
                    refs.append({'external_id': href.split('autosolar.es/')[-1][:120],
                                 'url': href, 'kind': seed['kind'],
                                 'nombre': (a.get('title') or '').strip()})
                nxt = doc.xpath('//link[@rel="next"]/@href') or doc.xpath('//a[@rel="next"]/@href')
                url = nxt[0] if nxt else None
                pages += 1
            logger.info('AutoSolar: %s fichas acumuladas tras %s (%s páginas)',
                        len(refs), seed['kind'], pages)
        return refs

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
                'power': _kw(_find(pairs, 'potencia', 'salida', 'continuada')
                             or _find(pairs, 'potencia', 'nominal')
                             or _find(pairs, 'potencia', 'salida')),
                'power_max': _kw(_find(pairs, 'potencia', 'maxima')),
                'vmax': _range_max(_find(pairs, 'rango', 'mpp')
                                   or _find(pairs, 'tension', 'maxima', 'entrada')
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

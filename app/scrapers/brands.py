"""Deducción y canonicalización de marca para scrapers de distribuidores.

`scraper_name` es la clave normalizada con la que se busca/crea el catálogo de la
marca; `KNOWN_BRANDS` mapea variantes tipográficas a un display canónico para no
fragmentar catálogos por diferencias triviales.
"""

import re
import unicodedata


def normalize_brand(raw):
    if not raw:
        return ''
    text = unicodedata.normalize('NFKD', str(raw))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace('-', ' ').replace('_', ' ')
    return re.sub(r'\s+', ' ', text).strip()


KNOWN_BRANDS = {
    'ja solar': 'JA Solar',
    'jasolar': 'JA Solar',
    'huawei': 'Huawei',
    'fronius': 'Fronius',
    'victron': 'Victron Energy',
    'victron energy': 'Victron Energy',
    'pylontech': 'Pylontech',
    'longi': 'LONGi',
    'trina': 'Trina Solar',
    'trina solar': 'Trina Solar',
    'canadian solar': 'Canadian Solar',
    'sma': 'SMA',
    'growatt': 'Growatt',
}


def _canonical(display):
    key = normalize_brand(display)
    if key in KNOWN_BRANDS:
        canonical = KNOWN_BRANDS[key]
        return canonical, normalize_brand(canonical)
    return display.strip(), key


def deduce_brand(attr, title):
    if attr and attr.strip():
        return _canonical(attr)
    key = normalize_brand(title)
    for alias, canonical in KNOWN_BRANDS.items():
        if alias in key:
            return canonical, normalize_brand(canonical)
    return None, None


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
    'longi green energy technology co ltd': 'LONGi',
    'trina solar coltd': 'Trina Solar',
    'csi solar co ltd': 'Canadian Solar',
    'jinko solar co ltd': 'Jinko Solar',
    'jinko': 'Jinko Solar',
    'risen energy co ltd': 'Risen',
    'risen': 'Risen',
    'qcells north america': 'Qcells',
    'hanwha q cells': 'Qcells',
    'rec group': 'REC',
    'maxeon solar technologies ltd': 'Maxeon',
    'phono solar technology co ltd': 'Phono Solar',
    'znshine pv tech co ltd': 'ZNShine',
    'wuxi suntech power co ltd': 'Suntech',
    'hengdian group dmegc magnetics co ltd': 'DMEGC',
    'leapton energy co ltd': 'Leapton',
    'peimar': 'Peimar',
    'exiom solution s a': 'Exiom',
    'hyundai energy solutions co ltd': 'Hyundai',
    'hd hyundai energy solutions co ltd': 'Hyundai',
    'seraphim solar system coltd': 'Seraphim',
    'yingli energy (china)': 'Yingli',
    'yingli energy development co ltd': 'Yingli',
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

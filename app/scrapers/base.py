
import re
from dataclasses import dataclass, field

VITAL = {
    'panel': ('nombre', 'power', 'voc', 'vmp', 'imp'),
    'inverter': ('nombre', 'power', 'vmax'),
    'battery': ('nombre', 'capacity_kwh', 'power_kw', 'voltage'),
    'wire': ('seccion', 'material'),
}


@dataclass
class NormalizedProduct:
    kind: str
    external_id: str
    source_url: str = ''
    fields: dict = field(default_factory=dict)
    brand: str = None

    def missing_vital(self):
        return [k for k in VITAL[self.kind] if self.fields.get(k) in (None, '')]

    @property
    def is_valid(self):
        return not self.missing_vital()


def to_float_eu(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def grab(text, labels, unit):
    low = text.lower()
    for label in labels:
        idx = low.find(label.lower())
        if idx == -1:
            continue
        segment = text[idx:idx + 140]
        m = re.search(r'([0-9][0-9.,]*)\s*' + unit, segment)
        if m:
            return to_float_eu(m.group(1))
    return None


def power_from_name(name):
    m = re.search(r'(\d+(?:[.,]\d+)?)', name or '')
    return to_float_eu(m.group(1)) if m else None

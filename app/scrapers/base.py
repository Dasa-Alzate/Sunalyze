
import re
from dataclasses import dataclass, field

VITAL = {
    'panel': ('nombre', 'power', 'voc', 'vmp', 'imp'),
    'inverter': ('nombre', 'power', 'vmax'),
    'battery': ('nombre', 'capacity_kwh', 'power_kw'),
    'wire': ('seccion', 'corriente', 'material'),
}


@dataclass
class NormalizedProduct:
    kind: str
    external_id: str
    source_url: str = ''
    fields: dict = field(default_factory=dict)
    brand: str = None
    notes: list = field(default_factory=list)

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


MAX_GAP = 28


def _segments(text, labels):
    low = text.lower()
    for label in labels:
        needle = label.lower()
        idx = low.find(needle)
        while idx != -1:
            end = idx + len(needle)
            yield text[end:end + MAX_GAP + 60]
            idx = low.find(needle, end)


_ALTERNATIVES = r'(?:\s*/\s*[0-9][0-9.,]*)*'


def grab(text, labels, unit, max_gap=MAX_GAP):
    pattern = re.compile(
        r'[^0-9]{0,%d}([0-9][0-9.,]*)%s\s*%s' % (max_gap, _ALTERNATIVES, unit)
    )
    for segment in _segments(text, labels):
        m = pattern.match(segment)
        if m:
            return to_float_eu(m.group(1))
    return None


def grab_range(text, labels, unit, max_gap=MAX_GAP):
    pattern = re.compile(
        r'[^0-9]{0,%d}([0-9][0-9.,]*)\s*[-–]\s*([0-9][0-9.,]*)\s*%s' % (max_gap, unit)
    )
    for segment in _segments(text, labels):
        m = pattern.match(segment)
        if m:
            return to_float_eu(m.group(1)), to_float_eu(m.group(2))
    return None, None


def power_from_name(name):
    m = re.search(r'(\d+(?:[.,]\d+)?)', name or '')
    return to_float_eu(m.group(1)) if m else None

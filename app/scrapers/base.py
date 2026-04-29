"""Contratos y utilidades de scraping, tolerantes a datos parciales.

La entrada NO es rígida: un `NormalizedProduct` lleva solo los campos que se
pudieron extraer. Solo se exige el conjunto VITAL por tipo; si falta algo vital
el producto se descarta (con motivo); lo no-vital ausente queda como null.
"""

import re
from dataclasses import dataclass, field

VITAL = {
    'panel': ('nombre', 'power', 'voc', 'vmp', 'imp'),
    'inverter': ('nombre', 'power', 'vmax'),
}


@dataclass
class NormalizedProduct:
    kind: str
    external_id: str
    source_url: str = ''
    fields: dict = field(default_factory=dict)

    def missing_vital(self):
        return [k for k in VITAL[self.kind] if self.fields.get(k) in (None, '')]

    @property
    def is_valid(self):
        return not self.missing_vital()


def to_float_eu(raw):
    """Convierte un número en convención europea/US a float.

    '96,9' -> 96.9 · '1.000,5' -> 1000.5 · '6.60' -> 6.6 · None -> None.
    """
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
    """Busca una etiqueta y captura el primer número seguido de `unit`.

    Salta cualificadores intermedios (p.ej. 'output current 240 V: 20,8 A' →
    devuelve 20.8, no 240). `unit` es un patrón regex ('V\\b', 'A\\b', '%').
    Devuelve None si no encuentra (campo ausente = válido si no es vital).
    """
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

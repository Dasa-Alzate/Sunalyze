"""Criterios de aceptación de hallazgos del scraper, centralizados y por capas.

Resolución por especificidad creciente (la última gana):
    global[tipo]  →  marca[marca][tipo]  →  equipo[external_id]

Cada capa aporta criterios parciales:
- `required`: campos que DEBEN venir (si una capa los define, reemplaza a la anterior).
- `ranges`: cotas de cordura por campo {campo: [min, max]} (merge por campo).

El servicio pregunta `evaluate(product, brand)` → lista de motivos de rechazo
(vacía = aceptado). Cambiar criterios = editar este fichero, no el scraper.
"""

from .base import VITAL

GLOBAL = {
    'panel': {
        'required': list(VITAL['panel']),
        'ranges': {
            'power': [50, 1000],
            'voc': [10, 120],
            'vmp': [5, 110],
            'imp': [1, 30],
            'isc': [1, 30],
            'y': [5, 30],
            'height': [500, 3000],
            'width': [300, 1500],
        },
    },
    'inverter': {
        'required': list(VITAL['inverter']),
        'ranges': {
            'power': [0.3, 300],
            'vmax': [100, 1500],
            'y': [80, 100],
            'I_max_input': [1, 200],
            'I_max_output': [1, 500],
        },
    },
}

BY_BRAND = {
    'fronius': {
        'inverter': {
            'required': ['nombre', 'power', 'vmax', 'y'],
        },
    },
}

BY_EQUIPMENT = {
}


def resolve(kind, brand, external_id=None):
    base = GLOBAL.get(kind, {})
    resolved = {'required': list(base.get('required', [])), 'ranges': dict(base.get('ranges', {}))}

    layers = []
    brand_layer = BY_BRAND.get((brand or '').lower(), {}).get(kind)
    if brand_layer:
        layers.append(brand_layer)
    if external_id and external_id in BY_EQUIPMENT:
        layers.append(BY_EQUIPMENT[external_id])

    for layer in layers:
        if 'required' in layer:
            resolved['required'] = list(layer['required'])
        if 'ranges' in layer:
            resolved['ranges'] = {**resolved['ranges'], **layer['ranges']}
    return resolved


def evaluate(product, brand):
    criteria = resolve(product.kind, brand, product.external_id)
    reasons = []
    for field in criteria['required']:
        if product.fields.get(field) in (None, ''):
            reasons.append(f'falta campo requerido: {field}')
    for field, bounds in criteria['ranges'].items():
        value = product.fields.get(field)
        if value is not None:
            lo, hi = bounds
            if not (lo <= value <= hi):
                reasons.append(f'{field}={value} fuera de rango [{lo}, {hi}]')
    return reasons

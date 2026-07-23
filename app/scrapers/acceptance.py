
from .base import VITAL

GLOBAL = {
    'panel': {
        'block': {
            'required': list(VITAL['panel']),
            'ranges': {
                'power': [10, 1200],
                'voc': [5, 150],
                'vmp': [3, 130],
                'imp': [0.5, 40],
                'y': [1, 40],
            },
        },
        'review': {
            'required': [],
            'ranges': {
                'power': [150, 800],
                'voc': [20, 100],
                'vmp': [20, 90],
                'imp': [3, 25],
                'isc': [3, 25],
                'y': [15, 30],
                'height': [800, 2600],
                'width': [600, 1400],
            },
        },
    },
    'inverter': {
        'block': {
            'required': list(VITAL['inverter']),
            'ranges': {
                'power': [0.1, 1000],
                'vmax': [50, 2000],
                'y': [50, 100],
            },
        },
        'review': {
            'required': [],
            'ranges': {
                'power': [0.5, 300],
                'vmax': [100, 1500],
                'y': [90, 100],
                'I_max_input': [1, 200],
                'I_max_output': [1, 500],
            },
        },
    },
    'battery': {
        'block': {
            'required': list(VITAL['battery']),
            'ranges': {
                'capacity_kwh': [0.5, 10000],
                'power_kw': [0.1, 5000],
                'voltage': [12, 2000],
                'round_trip_efficiency': [50, 100],
            },
        },
        'review': {
            'required': [],
            'ranges': {
                'capacity_kwh': [1, 50],
                'power_kw': [0.5, 30],
                'voltage': [40, 1000],
                'round_trip_efficiency': [85, 100],
                'dod': [50, 100],
            },
        },
    },
}

BY_BRAND = {
    'fronius': {
        'inverter': {
            'review': {
                'required': ['y'],
            },
        },
    },
}

BY_EQUIPMENT = {
}


def _merge(into, layer):
    if 'required' in layer:
        into['required'] = list(layer['required'])
    if 'ranges' in layer:
        into['ranges'] = {**into['ranges'], **layer['ranges']}


def resolve(kind, brand, external_id=None):
    base = GLOBAL.get(kind, {})
    resolved = {}
    for severity in ('block', 'review'):
        bucket = base.get(severity, {})
        resolved[severity] = {'required': list(bucket.get('required', [])),
                              'ranges': dict(bucket.get('ranges', {}))}

    layers = []
    brand_layer = BY_BRAND.get((brand or '').lower(), {}).get(kind)
    if brand_layer:
        layers.append(brand_layer)
    if external_id and external_id in BY_EQUIPMENT:
        layers.append(BY_EQUIPMENT[external_id])

    for layer in layers:
        for severity in ('block', 'review'):
            if severity in layer:
                _merge(resolved[severity], layer[severity])
    return resolved


def _violations(product, rules):
    reasons = []
    for field in rules['required']:
        if product.fields.get(field) in (None, ''):
            reasons.append(f'falta campo requerido: {field}')
    for field, bounds in rules['ranges'].items():
        value = product.fields.get(field)
        if value is not None:
            lo, hi = bounds
            if not (lo <= value <= hi):
                reasons.append(f'{field}={value} fuera de rango [{lo}, {hi}]')
    return reasons


def evaluate(product, brand):
    criteria = resolve(product.kind, brand, product.external_id)
    block = _violations(product, criteria['block'])
    review = _violations(product, criteria['review'])
    if block:
        verdict = 'blocked'
    elif review:
        verdict = 'review'
    else:
        verdict = 'accepted'
    return {'verdict': verdict, 'block': block, 'review': review}

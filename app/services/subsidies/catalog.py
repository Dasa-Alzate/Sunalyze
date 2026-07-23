
NACIONAL = {
    'irpf': {'pct': 0.40, 'base_max': 7500.0},
    'next_gen': {'eur_per_kwp': 600.0, 'cap_eur': 3000.0},
}

CCAA = {
    'andalucia': {
        'next_gen': {'eur_per_kwp': 600.0, 'cap_eur': 3000.0},
    },
    'cataluna': {
        'next_gen': {'eur_per_kwp': 600.0, 'cap_eur': 3500.0},
    },
    'comunidad valenciana': {
        'next_gen': {'eur_per_kwp': 650.0, 'cap_eur': 3000.0},
    },
    'comunidad de madrid': {
        'next_gen': {'eur_per_kwp': 600.0, 'cap_eur': 3000.0},
    },
}

MUNICIPIO = {
    'madrid': {
        'ibi': {'pct': 0.25, 'years': 3, 'annual_quota_eur': 400.0},
        'icio': {'pct': 0.95, 'base_ratio': 0.04},
    },
    'barcelona': {
        'ibi': {'pct': 0.50, 'years': 3, 'annual_quota_eur': 450.0},
        'icio': {'pct': 0.50, 'base_ratio': 0.04},
    },
    'valencia': {
        'ibi': {'pct': 0.50, 'years': 5, 'annual_quota_eur': 350.0},
        'icio': {'pct': 0.50, 'base_ratio': 0.04},
    },
}

_ACCENTS = str.maketrans('áàäâéèëêíìïîóòöôúùüûñ', 'aaaaeeeeiiiioooouuuun')


def _norm(value):
    if value is None:
        return None
    return value.strip().lower().translate(_ACCENTS)


def resolve(ccaa=None, municipio=None):
    resolved = {
        'irpf': dict(NACIONAL.get('irpf', {})),
        'next_gen': dict(NACIONAL.get('next_gen', {})),
    }
    ccaa_layer = CCAA.get(_norm(ccaa), {})
    if 'next_gen' in ccaa_layer:
        resolved['next_gen'] = {**resolved['next_gen'], **ccaa_layer['next_gen']}

    muni_layer = MUNICIPIO.get(_norm(municipio), {})
    if 'ibi' in muni_layer:
        resolved['ibi'] = dict(muni_layer['ibi'])
    if 'icio' in muni_layer:
        resolved['icio'] = dict(muni_layer['icio'])
    return resolved

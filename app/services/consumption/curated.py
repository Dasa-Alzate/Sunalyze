"""Perfiles de consumo curados (globales, org_id NULL).

Formas de 24h construidas con campanas gaussianas sobre niveles base, en pseudo-kWh:
el total diario de cada lista codifica el peso relativo del día (invierno vs verano,
laborable vs fin de semana), que la expansión conserva. Son estimaciones de dominio
razonables (literatura REE/IDAE), pensadas como punto de partida editable, no medidas.
"""

import math


def _shape(base, bumps, scale=1.0):
    hours = []
    for h in range(24):
        value = base
        for center, width, height in bumps:
            value += height * math.exp(-((h - center) ** 2) / (2.0 * width ** 2))
        hours.append(round(value * scale, 4))
    return hours


def _seasonal_daytypes(invierno, verano):
    return {
        'kind': 'seasonal',
        'payload': {
            'invierno': {'kind': 'daytypes', **invierno},
            'verano': {'kind': 'daytypes', **verano},
        },
    }


def curated_profiles():
    """Lista de perfiles de semilla: (nombre, kind, payload)."""
    residencial_tarde = {
        'laborable': _shape(0.25, [(8, 1.2, 0.5), (14, 1.5, 0.5), (21, 1.8, 1.4)]),
        'sabado': _shape(0.3, [(11, 2.5, 0.8), (21, 2.0, 1.2)]),
        'domingo': _shape(0.3, [(11, 2.5, 0.9), (20, 2.0, 1.0)]),
    }
    teletrabajo = {
        'laborable': _shape(0.25, [(13, 4.0, 0.9), (21, 1.8, 1.0)]),
        'sabado': _shape(0.3, [(12, 3.0, 0.8), (21, 2.0, 1.0)]),
    }
    oficina = {
        'laborable': _shape(0.15, [(13, 3.5, 1.6)]),
        'sabado': _shape(0.15, []),
    }
    comercio = {
        'laborable': _shape(0.2, [(15, 4.5, 1.5)]),
        'sabado': _shape(0.2, [(15, 4.5, 1.8)]),
        'domingo': _shape(0.2, [(13, 3.0, 0.6)]),
    }
    industrial = {
        'laborable': _shape(0.3, [(14, 6.0, 1.8)]),
        'sabado': _shape(0.3, [(11, 4.0, 0.6)]),
        'domingo': _shape(0.3, []),
    }
    riego = {
        'laborable': _shape(0.05, [(14, 3.0, 1.0)]),
    }

    def scaled(daytypes, factor):
        return {dt: [round(v * factor, 4) for v in hours] for dt, hours in daytypes.items()}

    return [
        ('Residencial tarde-noche', _seasonal_daytypes(scaled(residencial_tarde, 1.2), scaled(residencial_tarde, 0.85))),
        ('Residencial con teletrabajo', _seasonal_daytypes(scaled(teletrabajo, 1.15), scaled(teletrabajo, 0.9))),
        ('PYME oficina L-V', _seasonal_daytypes(scaled(oficina, 0.95), scaled(oficina, 1.1))),
        ('Comercio con fin de semana', _seasonal_daytypes(scaled(comercio, 1.0), scaled(comercio, 1.15))),
        ('Industrial dos turnos', _seasonal_daytypes(scaled(industrial, 1.0), scaled(industrial, 1.0))),
        ('Bombeo/riego diurno', _seasonal_daytypes(scaled(riego, 0.35), scaled(riego, 1.6))),
    ]

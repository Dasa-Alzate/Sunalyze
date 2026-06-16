"""Orquestacion de diagramas unifilares SVG: dominio, sin HTTP."""

from app.services.circuit import CircuitService
from app.errors import ValidationError


class CircuitDiagramService:

    REQUIRED_FIELDS = [
        'panel_model', 'panel_voc', 'panel_isc',
        'panels_per_string', 'num_strings',
        'dc_fuse_i', 'dc_switch_v', 'dc_cable_section',
    ]

    GENERATORS = {
        'cc-strings': CircuitService.generate_cc_vertical,
    }

    @classmethod
    def generate(cls, diagram_type, data):
        if diagram_type not in cls.GENERATORS:
            valid = ', '.join(cls.GENERATORS)
            raise ValidationError(f"Tipo desconocido: '{diagram_type}'. Válidos: {valid}")

        missing = [f for f in cls.REQUIRED_FIELDS if not str(data.get(f, '')).strip()]
        if missing:
            raise ValidationError('Parámetros obligatorios ausentes', details={'fields': missing})

        config = CircuitService.config_from_dict(data)
        return cls.GENERATORS[diagram_type](config)

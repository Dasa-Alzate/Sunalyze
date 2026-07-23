
from app.services.circuit import CircuitService
from app.errors import ValidationError


class CircuitDiagramService:

    REQUIRED_FIELDS = [
        'panel_model', 'panel_voc', 'panel_isc',
        'panels_per_string', 'num_strings',
        'dc_fuse_i', 'dc_switch_v', 'dc_cable_section',
    ]

    @classmethod
    def list_templates(cls):
        return CircuitService.list_templates()

    @classmethod
    def generate(cls, diagram_type, data):
        if not CircuitService.has_template(diagram_type):
            valid = ', '.join(t['name'] for t in CircuitService.list_templates())
            raise ValidationError(f"Tipo desconocido: '{diagram_type}'. Válidos: {valid}")

        missing = [f for f in cls.REQUIRED_FIELDS if not str(data.get(f, '')).strip()]
        if missing:
            raise ValidationError('Parámetros obligatorios ausentes', details={'fields': missing})

        config = CircuitService.config_from_dict(data)
        return CircuitService.generate_template(diagram_type, config)

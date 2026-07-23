
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.errors import ValidationError, NotFound


class DiagramaService:

    @staticmethod
    def build_template_vars(data):
        if not data or data.get('panel_id') in (None, ''):
            raise ValidationError("El campo 'panel_id' es requerido.")
        if data.get('inverter_id') in (None, ''):
            raise ValidationError("El campo 'inverter_id' es requerido.")

        panel = Panel.query.get(data['panel_id'])
        if not panel:
            raise NotFound('Panel no encontrado')

        inverter = Inverter.query.get(data['inverter_id'])
        if not inverter:
            raise NotFound('Inversor no encontrado')

        return {
            'panel': panel,
            'inverter': inverter,
            'field_power': data.get('field_power', '0'),
            'panel_amount': data.get('panel_amount', '0'),
            'needed_surface': data.get('needed_surface', '0'),
            'beta_optimal': data.get('beta_optimal', '0'),
            'max_panels_per_string': data.get('max_panels_per_string', '0'),
            'total_yield': data.get('total_yield', '0'),
            'first_section': data.get('first_section', '2x60mm²'),
            'second_section': data.get('second_section', '2x60mm²'),
            'first_length': data.get('first_length', ''),
            'second_length': data.get('second_length', ''),
            'panel_protection_v': data.get('panel_protection_v', ''),
            'panel_protection_i': data.get('panel_protection_i', ''),
        }

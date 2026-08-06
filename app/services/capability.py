
FIELD_LABELS = {
    ('panel', 'tcv'): 'Coeficiente de temperatura de Voc (β)',
    ('panel', 'tcp'): 'Coeficiente de temperatura de potencia (γ)',
    ('panel', 't_noct'): 'Temperatura nominal de operación (NOCT)',
    ('panel', 'isc'): 'Corriente de cortocircuito (Isc)',
    ('panel', 'vmp'): 'Tensión en el punto de máxima potencia (Vmp)',
    ('panel', 'imp'): 'Corriente en el punto de máxima potencia (Imp)',
    ('panel', 'max_series_fuse_a'): 'Calibre máximo de fusible en serie',
    ('panel', 'y'): 'Eficiencia del módulo',
    ('panel', 'height'): 'Alto del módulo',
    ('panel', 'width'): 'Ancho del módulo',
    ('inverter', 'y'): 'Eficiencia máxima del inversor',
    ('inverter', 'I_max_input'): 'Corriente máxima de entrada',
    ('inverter', 'I_max_output'): 'Corriente máxima de salida',
    ('inverter', 'power_max'): 'Potencia máxima aparente',
    ('inverter', 'mppt_v_min'): 'Tensión mínima de seguimiento MPP',
    ('inverter', 'mppt_v_max'): 'Tensión máxima de seguimiento MPP',
    ('inverter', 'mppt_count'): 'Número de seguidores MPP',
    ('inverter', 'isc_max_per_mppt'): 'Corriente de cortocircuito máxima por MPPT',
    ('battery', 'voltage'): 'Tensión nominal de la batería',
}

_EDIT_RESOURCE = {'panel': 'panels', 'inverter': 'inverters', 'battery': 'batteries'}


class CapabilityContext:

    def __init__(self):
        self.missing = []
        self.assumptions = []

    def value(self, row, entity, field, unlocks):
        raw = getattr(row, field, None)
        if raw is None:
            self._register_missing(row, entity, field, unlocks)
        return raw

    def value_or_assume(self, row, entity, field, fallback, reason, unlocks=None):
        raw = getattr(row, field, None)
        if raw is not None:
            return raw
        if unlocks:
            self._register_missing(row, entity, field, unlocks)
        self.assumptions.append({
            'entity': entity,
            'field': field,
            'label': FIELD_LABELS.get((entity, field), field),
            'used': fallback,
            'reason': reason,
        })
        return fallback

    def _register_missing(self, row, entity, field, unlocks):
        if any(m['entity'] == entity and m['field'] == field for m in self.missing):
            return
        resource = _EDIT_RESOURCE.get(entity, entity)
        self.missing.append({
            'entity': entity,
            'entity_id': getattr(row, 'id', None),
            'entity_nombre': getattr(row, 'nombre', None),
            'field': field,
            'label': FIELD_LABELS.get((entity, field), field),
            'unlocks': unlocks,
            'edit_url': f'/app/equipos?tab={resource}&edit={getattr(row, "id", "")}&field={field}',
        })

    def report(self, level, max_level='completo'):
        return {
            'detail_level': level,
            'max_detail_level': max_level,
            'missing': self.missing,
            'assumptions': self.assumptions,
        }

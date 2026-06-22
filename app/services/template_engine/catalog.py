"""Catálogo de variables: declaración de qué entidades/atributos son resolubles.

Es la única fuente de verdad de la whitelist (la usa el resolver para autorizar accesos) y a
la vez el metadato que la Fase 2 (editor) consumirá para ofrecer inserción de variables, en el
mismo espíritu que el registro de acciones del power-user. No ejecuta nada; es declarativo.

`propuesta_comercial` queda declarada con catálogo financiero vacío a la espera del módulo de
finanzas. La entidad `battery` se resuelve a vacío cuando el proyecto no tiene batería asignada.
"""


def _var(path, label, tipo):
    return {'path': path, 'label': label, 'tipo': tipo}


PROJECT_VARS = [
    _var('project.cliente', 'Cliente', 'text'),
    _var('project.direccion', 'Dirección', 'text'),
    _var('project.localidad', 'Localidad', 'text'),
    _var('project.estado', 'Estado', 'text'),
    _var('project.latitud', 'Latitud', 'number'),
    _var('project.longitud', 'Longitud', 'number'),
    _var('project.necesidad', 'Necesidad energética', 'number'),
    _var('project.autoconsumo', 'Autoconsumo', 'number'),
    _var('project.inclinacion', 'Inclinación', 'number'),
    _var('project.azimut', 'Azimut', 'number'),
    _var('project.potencia_contratada', 'Potencia contratada', 'number'),
    _var('project.cups', 'CUPS', 'text'),
    _var('project.compania', 'Compañía', 'text'),
    _var('project.referencia_catastral', 'Referencia catastral', 'text'),
    _var('project.tipo_voltaje', 'Tipo de voltaje', 'text'),
    _var('project.kwp', 'Potencia pico (kWp)', 'number'),
    _var('project.n_paneles', 'Número de paneles', 'number'),
]

PANEL_VARS = [
    _var('panel.nombre', 'Modelo del panel', 'text'),
    _var('panel.power', 'Potencia del panel (W)', 'number'),
    _var('panel.voc', 'Voc del panel (V)', 'number'),
    _var('panel.vmp', 'Vmp del panel (V)', 'number'),
    _var('panel.imp', 'Imp del panel (A)', 'number'),
    _var('panel.isc', 'Isc del panel (A)', 'number'),
    _var('panel.y', 'Eficiencia del panel (%)', 'number'),
    _var('panel.height', 'Alto del panel (mm)', 'number'),
    _var('panel.width', 'Ancho del panel (mm)', 'number'),
]

INVERTER_VARS = [
    _var('inverter.nombre', 'Modelo del inversor', 'text'),
    _var('inverter.power', 'Potencia AC del inversor (kW)', 'number'),
    _var('inverter.power_max', 'Potencia DC máx. (kW)', 'number'),
    _var('inverter.vmax', 'Voltaje DC máx. (V)', 'number'),
    _var('inverter.I_max_input', 'Corriente entrada máx. (A)', 'number'),
    _var('inverter.I_max_output', 'Corriente salida máx. (A)', 'number'),
    _var('inverter.y', 'Eficiencia del inversor (%)', 'number'),
]

BATTERY_VARS = [
    _var('battery.nombre', 'Modelo de la batería', 'text'),
    _var('battery.capacity_kwh', 'Capacidad nominal (kWh)', 'number'),
    _var('battery.usable_kwh', 'Capacidad útil (kWh)', 'number'),
    _var('battery.dod', 'Profundidad de descarga (%)', 'number'),
    _var('battery.power_kw', 'Potencia (kW)', 'number'),
    _var('battery.voltage', 'Voltaje (V)', 'number'),
    _var('battery.technology', 'Tecnología', 'text'),
    _var('battery.round_trip_efficiency', 'Eficiencia ida y vuelta (%)', 'number'),
    _var('battery.max_cycles', 'Ciclos máximos', 'number'),
]

WIRE_VARS = [
    _var('wire.seccion', 'Sección del cable (mm²)', 'number'),
    _var('wire.corriente', 'Corriente admisible (A)', 'number'),
    _var('wire.tipo', 'Tipo de cable', 'text'),
    _var('wire.material', 'Material conductor', 'text'),
    _var('wire.no_conductores', 'Número de conductores', 'number'),
]

USER_VARS = [
    _var('user.full_name', 'Nombre del usuario', 'text'),
    _var('user.first_name', 'Nombre', 'text'),
    _var('user.last_name', 'Apellidos', 'text'),
    _var('user.email', 'Correo del usuario', 'text'),
]

ORG_VARS = [
    _var('org.nombre', 'Nombre de la organización', 'text'),
    _var('org.type', 'Tipo de organización', 'text'),
    _var('org.plan', 'Plan', 'text'),
]

_PROJECT_GROUPS = [
    {'entity': 'project', 'label': 'Proyecto', 'vars': PROJECT_VARS},
    {'entity': 'panel', 'label': 'Panel', 'vars': PANEL_VARS},
    {'entity': 'inverter', 'label': 'Inversor', 'vars': INVERTER_VARS},
    {'entity': 'battery', 'label': 'Batería', 'vars': BATTERY_VARS},
    {'entity': 'wire', 'label': 'Cableado', 'vars': WIRE_VARS},
    {'entity': 'user', 'label': 'Usuario', 'vars': USER_VARS},
    {'entity': 'org', 'label': 'Organización', 'vars': ORG_VARS},
]

VARIABLE_CATALOG = {
    'memoria_calculo': _PROJECT_GROUPS,
    'documento_legal': _PROJECT_GROUPS,
    'analisis_caso': _PROJECT_GROUPS,
    'propuesta_comercial': _PROJECT_GROUPS,
}


def variable_catalog(kind):
    """Grupos de variables disponibles para un DocumentKind (para el editor de Fase 2)."""
    return VARIABLE_CATALOG.get(kind, [])


def whitelist():
    """Mapa entidad -> set de atributos resolubles, derivado del catálogo."""
    allowed = {}
    for group in _PROJECT_GROUPS:
        attrs = set()
        for v in group['vars']:
            attrs.add(v['path'].split('.', 1)[1])
        allowed[group['entity']] = attrs
    return allowed

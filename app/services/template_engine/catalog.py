"""Catálogo de variables: declaración de qué entidades/atributos son resolubles.

Es la única fuente de verdad de la whitelist (la usa el resolver para autorizar accesos) y a
la vez el metadato que el editor consume para ofrecer inserción de variables. No ejecuta nada;
es declarativo.

Los grupos de variables se nombran (`GROUPS`) y cada `DocumentKind` declara qué grupos expone
(`var_groups` en el registro de `DocumentKind`): así el catálogo por kind se deriva del registro
y añadir un kind es una sola entrada. Las labels de `finance.*` son neutras (la moneda la pone
el filtro `money` según la jurisdicción). Las entidades opcionales (`battery`, `wire`,
`installation`, `maintenance`, `incident`) resuelven a vacío cuando no existen.
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

FINANCE_VARS = [
    _var('finance.net_capex', 'CAPEX neto', 'number'),
    _var('finance.annual_saving_year1_eur', 'Ahorro anual año 1', 'number'),
    _var('finance.payback_years', 'Payback simple (años)', 'number'),
    _var('finance.payback_discounted_years', 'Payback descontado (años)', 'number'),
    _var('finance.irr', 'TIR', 'number'),
    _var('finance.npv', 'VAN', 'number'),
    _var('finance.lcoe', 'LCOE (por kWh)', 'number'),
    _var('finance.co2_avoided_year', 'CO₂ evitado año 1 (kg)', 'number'),
    _var('finance.incentives_total', 'Total incentivos', 'number'),
]

INSTALLATION_VARS = [
    _var('installation.status', 'Estado de la instalación', 'text'),
    _var('installation.commissioned_at', 'Fecha de puesta en marcha', 'date'),
    _var('installation.warranty_until', 'Garantía hasta', 'date'),
    _var('installation.expected_annual_kwh', 'Producción anual esperada (kWh)', 'number'),
    _var('installation.notes', 'Notas de la instalación', 'text'),
]

MAINTENANCE_VARS = [
    _var('maintenance.kind', 'Tipo de mantenimiento', 'text'),
    _var('maintenance.status', 'Estado del mantenimiento', 'text'),
    _var('maintenance.scheduled_at', 'Fecha programada', 'date'),
    _var('maintenance.done_at', 'Fecha realizada', 'date'),
    _var('maintenance.technician', 'Técnico', 'text'),
    _var('maintenance.notes', 'Notas del mantenimiento', 'text'),
]

INCIDENT_VARS = [
    _var('incident.title', 'Título de la incidencia', 'text'),
    _var('incident.description', 'Descripción de la incidencia', 'text'),
    _var('incident.severity', 'Severidad', 'text'),
    _var('incident.status', 'Estado de la incidencia', 'text'),
    _var('incident.opened_at', 'Fecha de apertura', 'date'),
    _var('incident.resolved_at', 'Fecha de resolución', 'date'),
]


GROUPS = {
    'project': {'entity': 'project', 'label': 'Proyecto', 'vars': PROJECT_VARS},
    'panel': {'entity': 'panel', 'label': 'Panel', 'vars': PANEL_VARS},
    'inverter': {'entity': 'inverter', 'label': 'Inversor', 'vars': INVERTER_VARS},
    'battery': {'entity': 'battery', 'label': 'Batería', 'vars': BATTERY_VARS},
    'wire': {'entity': 'wire', 'label': 'Cableado', 'vars': WIRE_VARS},
    'user': {'entity': 'user', 'label': 'Usuario', 'vars': USER_VARS},
    'org': {'entity': 'org', 'label': 'Organización', 'vars': ORG_VARS},
    'finance': {'entity': 'finance', 'label': 'Finanzas', 'vars': FINANCE_VARS},
    'installation': {'entity': 'installation', 'label': 'Instalación', 'vars': INSTALLATION_VARS},
    'maintenance': {'entity': 'maintenance', 'label': 'Mantenimiento', 'vars': MAINTENANCE_VARS},
    'incident': {'entity': 'incident', 'label': 'Incidencia', 'vars': INCIDENT_VARS},
}


def _kind_var_groups(kind):
    from app.models.report_template import document_kind_var_groups
    return document_kind_var_groups(kind)


def variable_catalog(kind):
    """Grupos de variables disponibles para un DocumentKind, según su registro."""
    return [GROUPS[name] for name in _kind_var_groups(kind) if name in GROUPS]


def variable_catalog_all():
    """Catálogo completo por kind (entidad -> grupos), derivado del registro de DocumentKind."""
    from app.models.report_template import DocumentKind
    return {key: variable_catalog(key) for key in DocumentKind.ALL}


def whitelist():
    """Mapa entidad -> set de atributos resolubles, derivado de todos los grupos."""
    allowed = {}
    for group in GROUPS.values():
        attrs = set()
        for v in group['vars']:
            attrs.add(v['path'].split('.', 1)[1])
        allowed[group['entity']] = attrs
    return allowed

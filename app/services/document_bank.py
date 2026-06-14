"""Siembra del banco oficial de tipos de documento del instalador FV (España).

Define el catálogo de plantillas oficiales (`OFFICIAL_TEMPLATES_ES`) — cada una con su
`kind`, sus tags (`country`, `required_by`, `stage`) y su contenido por secciones con
expresiones del motor de variables — y un sembrador idempotente que las materializa como
plantillas system (`org_id` NULL, `scope='system'`, `is_official=True`, `status='published'`)
con una `TemplateVersion` v1 publicada.

Es dominio puro (sin Flask): lo consume el CLI `flask docs seed` y los tests. La idempotencia
se basa en la identidad lógica `(kind, name, country)`: si ya existe una plantilla system con
esa terna, se omite; nunca se duplica ni se sobrescribe.
"""

from datetime import datetime

from app.extensions import db
from app.models.report_template import ReportTemplate, TemplateVersion


def _s(section_id, title, body, section_type='text'):
    return {'id': section_id, 'type': section_type, 'title': title, 'body': body}


OFFICIAL_TEMPLATES_ES = [
    {
        'kind': 'memoria_calculo',
        'name': 'Memoria técnica de diseño',
        'description': 'Memoria técnica de diseño de la instalación FV (REBT / ITC-BT-40).',
        'required_by': 'Distribuidora / Industria',
        'stage': 'legalizacion',
        'content': [
            _s('datos', 'Datos de la instalación',
               'Titular: {{ project.cliente }}\n'
               'Emplazamiento: {{ project.direccion }}, {{ project.localidad }}\n'
               'Referencia catastral: {{ project.referencia_catastral }}\n'
               'CUPS: {{ project.cups }}\n'
               'Compañía distribuidora: {{ project.compania }}\n'
               'Potencia contratada: {{ project.potencia_contratada | number(2) }} kW'),
            _s('generador', 'Generador fotovoltaico',
               'Módulo: {{ panel.nombre }} de {{ panel.power | number(0) }} Wp.\n'
               'Número de módulos: {{ project.n_paneles | number(0) }}.\n'
               'Potencia pico del campo: {{ project.kwp | number(2) }} kWp.\n'
               'Voc del módulo: {{ panel.voc | number(2) }} V — Isc: {{ panel.isc | number(2) }} A.\n'
               'Inclinación: {{ project.inclinacion | number(0) }}° — Azimut: {{ project.azimut | number(0) }}°.'),
            _s('inversor', 'Inversor',
               'Inverter: {{ inverter.nombre }}.\n'
               'Potencia AC: {{ inverter.power | number(2) }} kW.\n'
               'Voltaje DC máximo: {{ inverter.vmax | number(0) }} V.\n'
               'Ratio DC/AC: {{ round(project.kwp / inverter.power, 2) | number(2) }}.'),
            _s('acumulacion', 'Acumulación',
               'Batería: {{ battery.nombre }}.\n'
               'Capacidad útil: {{ battery.usable_kwh | number(2) }} kWh.\n'
               'Tecnología: {{ battery.technology }}.'),
        ],
    },
    {
        'kind': 'solicitud_conexion',
        'name': 'Solicitud de acceso y conexión',
        'description': 'Solicitud de acceso y conexión a red para autoconsumo (RD 244/2019).',
        'required_by': 'Distribuidora',
        'stage': 'legalizacion',
        'content': [
            _s('solicitante', 'Datos del solicitante',
               'Titular del suministro: {{ project.cliente }}\n'
               'Dirección: {{ project.direccion }}, {{ project.localidad }}\n'
               'CUPS: {{ project.cups }}\n'
               'Compañía distribuidora: {{ project.compania }}'),
            _s('instalacion', 'Datos de la instalación de generación',
               'Potencia pico: {{ project.kwp | number(2) }} kWp.\n'
               'Potencia nominal del inverter: {{ inverter.power | number(2) }} kW.\n'
               'Tipo de voltaje: {{ project.tipo_voltaje }}.\n'
               'Potencia contratada actual: {{ project.potencia_contratada | number(2) }} kW.'),
            _s('modalidad', 'Modalidad de autoconsumo',
               'Modalidad solicitada: autoconsumo con excedentes.\n'
               'Coordenadas del punto de conexión: '
               '{{ project.latitud | number(5) }}, {{ project.longitud | number(5) }}.'),
        ],
    },
    {
        'kind': 'certificado',
        'name': 'Certificado de Instalación Eléctrica (CIE)',
        'description': 'Boletín / Certificado de Instalación Eléctrica para Industria de la CCAA.',
        'required_by': 'Industria / CCAA',
        'stage': 'legalizacion',
        'content': [
            _s('identificacion', 'Identificación de la instalación',
               'Titular: {{ project.cliente }}\n'
               'Emplazamiento: {{ project.direccion }}, {{ project.localidad }}\n'
               'CUPS: {{ project.cups }}'),
            _s('caracteristicas', 'Características técnicas',
               'Potencia instalada: {{ project.kwp | number(2) }} kWp.\n'
               'Inverter: {{ inverter.nombre }} — {{ inverter.power | number(2) }} kW.\n'
               'Tipo de voltaje: {{ project.tipo_voltaje }}.'),
            _s('declaracion', 'Declaración del instalador',
               'El instalador autorizado certifica que la instalación cumple el REBT y sus '
               'instrucciones técnicas complementarias (ITC-BT-40) y queda apta para su '
               'puesta en servicio. Firmado: {{ user.full_name }} ({{ org.nombre }}).'),
        ],
    },
    {
        'kind': 'documento_legal',
        'name': 'Estudio estructural de cubierta',
        'description': 'Verificación estructural de la cubierta frente a la sobrecarga FV (CTE DB-SE).',
        'required_by': 'Cliente / Normativa',
        'stage': 'diseno',
        'content': [
            _s('emplazamiento', 'Emplazamiento',
               'Cliente: {{ project.cliente }}\n'
               'Dirección: {{ project.direccion }}, {{ project.localidad }}\n'
               'Referencia catastral: {{ project.referencia_catastral }}'),
            _s('cargas', 'Cargas del campo fotovoltaico',
               'Número de módulos: {{ project.n_paneles | number(0) }}.\n'
               'Dimensiones del módulo: {{ panel.width | number(0) }} x {{ panel.height | number(0) }} mm.\n'
               'Potencia pico total: {{ project.kwp | number(2) }} kWp.'),
            _s('conclusion', 'Conclusión',
               'Conforme al CTE DB-SE, la cubierta admite la sobrecarga permanente añadida por '
               'la estructura soporte y los módulos sin superar los estados límite de servicio. '
               'Inclinación de montaje prevista: {{ project.inclinacion | number(0) }}°.'),
        ],
    },
    {
        'kind': 'contrato',
        'name': 'Contrato de instalación',
        'description': 'Contrato de suministro e instalación de la instalación FV.',
        'required_by': 'Cliente',
        'stage': 'diseno',
        'content': [
            _s('partes', 'Partes',
               'Instalador: {{ org.nombre }}, representado por {{ user.full_name }}.\n'
               'Cliente: {{ project.cliente }}, con domicilio en {{ project.direccion }}, '
               '{{ project.localidad }}.'),
            _s('objeto', 'Objeto del contrato',
               'Suministro e instalación de un sistema FV de {{ project.kwp | number(2) }} kWp '
               'con {{ project.n_paneles | number(0) }} módulos {{ panel.nombre }} e inverter '
               '{{ inverter.nombre }} en el emplazamiento indicado.'),
            _s('precio', 'Precio',
               'Importe total de la instalación: {{ finance.net_capex | money(2) }}.\n'
               'Ahorro anual estimado (año 1): {{ finance.annual_saving_year1_eur | money(2) }}.'),
            _s('condiciones', 'Condiciones',
               'Plazos, forma de pago y obligaciones de las partes según las cláusulas anexas. '
               'Firmado en conformidad por ambas partes.'),
        ],
    },
    {
        'kind': 'contrato',
        'name': 'Contrato de mantenimiento',
        'description': 'Contrato de mantenimiento preventivo y correctivo de la instalación FV.',
        'required_by': 'Cliente',
        'stage': 'posventa',
        'content': [
            _s('partes', 'Partes',
               'Prestador del servicio: {{ org.nombre }}.\n'
               'Cliente: {{ project.cliente }} — {{ project.direccion }}, {{ project.localidad }}.'),
            _s('alcance', 'Alcance del servicio',
               'Mantenimiento de la instalación de {{ project.kwp | number(2) }} kWp '
               '(inverter {{ inverter.nombre }}).\n'
               'Estado actual de la instalación: {{ installation.status }}.\n'
               'Producción anual esperada: {{ installation.expected_annual_kwh | number(0) }} kWh.'),
            _s('condiciones', 'Condiciones económicas',
               'Cuota anual del servicio: {{ finance.annual_saving_year1_eur | money(2) }} '
               '(referencia de ahorro). Revisiones preventivas periódicas y atención '
               'correctiva ante incidencias.'),
        ],
    },
    {
        'kind': 'certificado',
        'name': 'Certificado de garantía',
        'description': 'Certificado de garantía de los equipos y de la instalación.',
        'required_by': 'Cliente',
        'stage': 'entrega',
        'content': [
            _s('beneficiario', 'Beneficiario',
               'Cliente: {{ project.cliente }}\n'
               'Instalación en: {{ project.direccion }}, {{ project.localidad }}'),
            _s('cobertura', 'Cobertura',
               'Módulos: {{ panel.nombre }} ({{ project.n_paneles | number(0) }} uds).\n'
               'Inverter: {{ inverter.nombre }}.\n'
               'Potencia garantizada del campo: {{ project.kwp | number(2) }} kWp.'),
            _s('vigencia', 'Vigencia',
               'Garantía de la instalación vigente hasta {{ installation.warranty_until | date }}. '
               'Emitido por {{ org.nombre }}.'),
        ],
    },
    {
        'kind': 'certificado',
        'name': 'Certificado energético (deducción IRPF)',
        'description': 'Justificante de mejora energética para la deducción de IRPF.',
        'required_by': 'Hacienda',
        'stage': 'entrega',
        'content': [
            _s('titular', 'Titular de la vivienda',
               'Cliente: {{ project.cliente }}\n'
               'Vivienda: {{ project.direccion }}, {{ project.localidad }}\n'
               'Referencia catastral: {{ project.referencia_catastral }}'),
            _s('actuacion', 'Actuación de mejora energética',
               'Instalación de autoconsumo FV de {{ project.kwp | number(2) }} kWp.\n'
               'Producción anual esperada: {{ installation.expected_annual_kwh | number(0) }} kWh.\n'
               'CO₂ evitado (año 1): {{ finance.co2_avoided_year | number(0) }} kg.'),
            _s('justificacion', 'Justificación de la deducción',
               'La actuación reduce la demanda de energía primaria no renovable de la vivienda, '
               'a efectos de la deducción de IRPF por obras de mejora de la eficiencia '
               'energética. Importe de la inversión: {{ finance.net_capex | money(2) }}.'),
        ],
    },
    {
        'kind': 'certificado',
        'name': 'Acta de puesta en marcha y entrega',
        'description': 'Acta de puesta en marcha y entrega de la instalación al cliente.',
        'required_by': 'Cliente',
        'stage': 'entrega',
        'content': [
            _s('identificacion', 'Identificación',
               'Cliente: {{ project.cliente }}\n'
               'Emplazamiento: {{ project.direccion }}, {{ project.localidad }}\n'
               'CUPS: {{ project.cups }}'),
            _s('puesta_marcha', 'Puesta en marcha',
               'Fecha de puesta en marcha: {{ installation.commissioned_at | date }}.\n'
               'Estado de la instalación: {{ installation.status }}.\n'
               'Producción anual esperada: {{ installation.expected_annual_kwh | number(0) }} kWh.\n'
               'Garantía hasta: {{ installation.warranty_until | date }}.'),
            _s('conformidad', 'Conformidad',
               'Se entrega la instalación de {{ project.kwp | number(2) }} kWp en funcionamiento '
               'y a plena conformidad del cliente. Por {{ org.nombre }}: {{ user.full_name }}. '
               'Observaciones: {{ installation.notes }}.'),
        ],
    },
    {
        'kind': 'informe_mantenimiento',
        'name': 'Informe de mantenimiento',
        'description': 'Informe de una visita de mantenimiento sobre la instalación.',
        'required_by': 'Cliente',
        'stage': 'posventa',
        'content': [
            _s('instalacion', 'Instalación',
               'Cliente: {{ project.cliente }} — {{ project.direccion }}, {{ project.localidad }}.\n'
               'Estado: {{ installation.status }}.\n'
               'Producción anual esperada: {{ installation.expected_annual_kwh | number(0) }} kWh.'),
            _s('visita', 'Visita de mantenimiento',
               'Tipo: {{ maintenance.kind }}.\n'
               'Estado de la visita: {{ maintenance.status }}.\n'
               'Fecha programada: {{ maintenance.scheduled_at | date }}.\n'
               'Fecha realizada: {{ maintenance.done_at | date }}.\n'
               'Técnico: {{ maintenance.technician }}.\n'
               'Observaciones: {{ maintenance.notes }}.'),
            _s('incidencia', 'Incidencia relevante',
               'Título: {{ incident.title }}.\n'
               'Severidad: {{ incident.severity }} — Estado: {{ incident.status }}.\n'
               'Apertura: {{ incident.opened_at | date }} — Resolución: {{ incident.resolved_at | date }}.\n'
               'Descripción: {{ incident.description }}.'),
        ],
    },
    {
        'kind': 'propuesta_comercial',
        'name': 'Propuesta comercial y estudio de ahorro',
        'description': 'Oferta económica con métricas financieras del proyecto FV.',
        'required_by': 'Cliente',
        'stage': 'diseno',
        'content': [
            _s('cliente', 'Propuesta para',
               'Cliente: {{ project.cliente }}\n'
               'Emplazamiento: {{ project.direccion }}, {{ project.localidad }}'),
            _s('solucion', 'Solución propuesta',
               'Sistema FV de {{ project.kwp | number(2) }} kWp con '
               '{{ project.n_paneles | number(0) }} módulos {{ panel.nombre }} e inverter '
               '{{ inverter.nombre }}.'),
            _s('economia', 'Estudio económico',
               'Inversión (CAPEX neto): {{ finance.net_capex | money(2) }}.\n'
               'Ahorro anual (año 1): {{ finance.annual_saving_year1_eur | money(2) }}.\n'
               'Payback simple: {{ finance.payback_years | number(1) }} años.\n'
               'TIR: {{ finance.irr | number(2) }} — VAN: {{ finance.npv | money(2) }}.\n'
               'CO₂ evitado (año 1): {{ finance.co2_avoided_year | number(0) }} kg.'),
        ],
    },
]


class DocumentBankSeeder:
    """Materializa el banco oficial de plantillas ES de forma idempotente."""

    COUNTRY = 'ES'
    LOCALE = 'es'
    CURRENCY = 'EUR'

    @staticmethod
    def _exists(kind, name, country):
        return (ReportTemplate.query
                .filter(ReportTemplate.org_id.is_(None),
                        ReportTemplate.scope == 'system',
                        ReportTemplate.kind == kind,
                        ReportTemplate.name == name,
                        ReportTemplate.country == country)
                .first())

    @classmethod
    def seed(cls, specs=None):
        """Crea las plantillas oficiales que falten. Devuelve {created, skipped}."""
        specs = specs if specs is not None else OFFICIAL_TEMPLATES_ES
        created = 0
        skipped = 0
        now = datetime.utcnow()
        for spec in specs:
            if cls._exists(spec['kind'], spec['name'], cls.COUNTRY):
                skipped += 1
                continue
            template = ReportTemplate(
                org_id=None,
                scope='system',
                kind=spec['kind'],
                name=spec['name'],
                description=spec.get('description', ''),
                country=cls.COUNTRY,
                locale=cls.LOCALE,
                currency=cls.CURRENCY,
                required_by=spec['required_by'],
                stage=spec['stage'],
                status='published',
                is_official=True,
            )
            db.session.add(template)
            db.session.flush()
            version = TemplateVersion(
                template_id=template.id,
                version=1,
                changelog='Versión inicial del banco oficial',
                published_at=now,
            )
            version.content = spec['content']
            db.session.add(version)
            created += 1
        db.session.commit()
        return {'created': created, 'skipped': skipped}

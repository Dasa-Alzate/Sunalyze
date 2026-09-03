"""Catalogo estatico de tramitacion de legalizacion por comunidad autonoma.

Fuentes oficiales verificadas en julio de 2026; ver docs/legalizacion-ccaa-research.md.
Las claves de CCAA se normalizan igual que en subsidies.catalog (minusculas, sin acentos).
"""

_ACCENTS = str.maketrans('áàäâéèëêíìïîóòöôúùüûñ', 'aaaaeeeeiiiioooouuuun')


def _norm(value):
    if not value:
        return ''
    return str(value).strip().lower().translate(_ACCENTS)


CATALOG = {
    'comunitat valenciana': {
        'nombre': 'Comunitat Valenciana',
        'organismo': 'Conselleria competente en Industria — Generalitat Valenciana',
        'plataforma': 'Sede electronica de la GVA (tramitacion exclusivamente telematica)',
        'autenticacion': (
            'Firma electronica avanzada o cualificada (DNIe, FNMT, ACCV, Cl@ve Firma) '
            'del instalador habilitado, del titular o de su representante legal.'
        ),
        'resultado': (
            'Justificante de registro y numero de expediente, disponibles despues '
            'en la Carpeta Ciudadana.'
        ),
        'mtd_oficial': 'gva_pdf',
        'procedimientos': [
            {
                'codigo': 'PROP 440',
                'nombre': 'Instalaciones electricas de baja tension que requieren memoria tecnica de diseno (alta, modificacion, baja, cambio de titularidad)',
                'url': 'https://sede.gva.es/es/detall-tramit?id_proc=440',
            },
            {
                'codigo': 'PROP 18168',
                'nombre': 'Generacion en baja tension para autoconsumo con potencia instalada menor o igual a 10 kW: comunicacion de alta e inscripcion en el registro de autoconsumo (exclusivamente telematico por instalador habilitado)',
                'url': 'https://www.gva.es/es/inicio/procedimientos?id_proc=18168',
            },
            {
                'codigo': 'PROP 2889',
                'nombre': 'Puesta en servicio e inscripcion en el registro de produccion, procedimiento simplificado para instalaciones de hasta 100 kW conectadas en baja tension',
                'url': 'https://sede.gva.es/es/detall-tramit?id_proc=2889',
            },
        ],
        'impresos': [
            {
                'codigo': 'MTD (modelo 23167)',
                'nombre': 'Memoria tecnica de diseno, modelo oficial bilingue (rev. 29/09/22)',
                'url': 'https://www.gva.es/downloads/publicados/IN/23167_BI.pdf',
                'generable': True,
            },
            {
                'codigo': 'MEMTECDI (modelo 23224)',
                'nombre': 'Memoria tecnica de diseno a titular',
                'url': 'https://www.gva.es/downloads/publicados/IN/23224_BI.pdf',
                'generable': False,
            },
        ],
        'pasos': [
            'Preparar la memoria tecnica de diseno en el modelo oficial de la GVA y el resto de adjuntos (esquema unifilar, croquis de trazado, certificado de instalacion CIE).',
            'Solicitar el CAU a la distribuidora y, si procede, el permiso de acceso y conexion antes de ejecutar.',
            'Acceder al procedimiento telematico de la sede de la GVA con certificado digital.',
            'Rellenar los formularios web de datos generales, tipo de instalacion y certificado, y adjuntar la MTD y el resto de documentos.',
            'Firmar y presentar; descargar el justificante de registro.',
            'Anotar el numero de expediente que aparece en la Carpeta Ciudadana.',
        ],
        'presentacion': [
            {
                'seccion': 'A. Titular',
                'campos': [
                    {'label': 'Nombre y apellidos o razon social', 'key': 'cliente'},
                    {'label': 'Domicilio', 'key': 'direccion'},
                    {'label': 'Localidad', 'key': 'localidad'},
                    {'label': 'Provincia', 'key': 'provincia'},
                ],
            },
            {
                'seccion': 'B. Emplazamiento y generacion',
                'campos': [
                    {'label': 'Emplazamiento de la instalacion', 'key': 'direccion'},
                    {'label': 'Referencia catastral', 'key': 'referencia_catastral'},
                    {'label': 'Potencia nominal del inversor (kW)', 'key': 'potencia_inversor'},
                    {'label': 'Potencia instalada / pico (kWp)', 'key': 'kwp'},
                    {'label': 'Numero de modulos', 'key': 'n_paneles'},
                ],
            },
            {
                'seccion': 'Contrato electrico',
                'campos': [
                    {'label': 'CUPS', 'key': 'cups'},
                    {'label': 'Empresa distribuidora / comercializadora', 'key': 'compania'},
                    {'label': 'Potencia contratada (kW)', 'key': 'potencia_contratada'},
                    {'label': 'Tipo de suministro (monofasico/trifasico)', 'key': 'tipo_voltaje'},
                ],
            },
            {
                'seccion': 'Equipos',
                'campos': [
                    {'label': 'Modulo fotovoltaico', 'key': 'panel_nombre'},
                    {'label': 'Inversor', 'key': 'inverter_nombre'},
                    {'label': 'Bateria', 'key': 'battery_nombre'},
                ],
            },
        ],
    },
    'murcia': {
        'nombre': 'Region de Murcia',
        'organismo': 'Direccion General competente en Energia — CARM',
        'plataforma': 'Sede electronica de la CARM (declaracion responsable telematica)',
        'autenticacion': (
            'Certificado digital en la sede electronica de la CARM; la tasa se liquida '
            'durante la propia presentacion y se paga con tarjeta.'
        ),
        'resultado': (
            'Inscripcion en el registro de instalaciones electricas de baja tension con '
            'numero de expediente/registro; en la declaracion responsable se ratifica al '
            'redactor de la memoria tecnica de diseno.'
        ),
        'mtd_oficial': 'carm_html',
        'procedimientos': [
            {
                'codigo': '0019',
                'nombre': 'Registro de instalaciones electricas de baja tension (declaracion responsable)',
                'url': 'https://sede.carm.es/web/pagina?IDCONTENIDO=19&IDTIPO=240',
            },
            {
                'codigo': 'Produccion',
                'nombre': 'Registro administrativo de instalaciones de produccion de energia electrica',
                'url': 'https://sede.carm.es/web/pagina?IDCONTENIDO=4659&IDTIPO=240',
            },
            {
                'codigo': 'MUI',
                'nombre': 'Portal informativo de tramitacion de instalaciones de autoconsumo (MUI)',
                'url': 'https://mui.carm.es/web/mui/informacion-tramitacion-instalaciones-autoconsumo',
            },
        ],
        'impresos': [
            {
                'codigo': 'MTD IEBT',
                'nombre': 'Memoria tecnica de diseno de instalaciones electricas de baja tension (modelo junio 2021, Word)',
                'url': 'https://sede.carm.es/documentos/19/Memoria%20t%C3%A9cnica%20de%20dise%C3%B1o%20IEBT%20(Junio-2021).doc',
                'generable': True,
            },
            {
                'codigo': 'CIE BT',
                'nombre': 'Certificado de instalacion electrica de baja tension',
                'url': 'https://sede.carm.es/documentos/1064/Certificado%20de%20instalaci%C3%B3n%20el%C3%A9ctrica%20de%20baja%20tensi%C3%B3n.docx',
                'generable': False,
            },
        ],
        'pasos': [
            'Preparar la memoria tecnica de diseno siguiendo el modelo IEBT de la CARM y el certificado de instalacion (CIE).',
            'Solicitar el CAU a la distribuidora y, si procede, el permiso de acceso y conexion antes de ejecutar.',
            'Acceder al procedimiento 0019 de la sede electronica de la CARM con certificado digital.',
            'Cumplimentar la declaracion responsable, ratificando al redactor de la memoria tecnica, y adjuntar la documentacion.',
            'Liquidar la tasa durante la presentacion (pago con tarjeta) y firmar.',
            'Anotar el numero de expediente/registro del justificante.',
        ],
        'presentacion': [
            {
                'seccion': 'Titular',
                'campos': [
                    {'label': 'Nombre y apellidos o razon social', 'key': 'cliente'},
                    {'label': 'Domicilio', 'key': 'direccion'},
                    {'label': 'Localidad', 'key': 'localidad'},
                    {'label': 'Provincia', 'key': 'provincia'},
                ],
            },
            {
                'seccion': 'Instalacion',
                'campos': [
                    {'label': 'Emplazamiento', 'key': 'direccion'},
                    {'label': 'Referencia catastral', 'key': 'referencia_catastral'},
                    {'label': 'Potencia instalada / pico (kWp)', 'key': 'kwp'},
                    {'label': 'Numero de modulos', 'key': 'n_paneles'},
                    {'label': 'Potencia nominal del inversor (kW)', 'key': 'potencia_inversor'},
                ],
            },
            {
                'seccion': 'Contrato electrico',
                'campos': [
                    {'label': 'CUPS', 'key': 'cups'},
                    {'label': 'Empresa distribuidora / comercializadora', 'key': 'compania'},
                    {'label': 'Potencia contratada (kW)', 'key': 'potencia_contratada'},
                    {'label': 'Tipo de suministro (monofasico/trifasico)', 'key': 'tipo_voltaje'},
                ],
            },
            {
                'seccion': 'Equipos',
                'campos': [
                    {'label': 'Modulo fotovoltaico', 'key': 'panel_nombre'},
                    {'label': 'Inversor', 'key': 'inverter_nombre'},
                    {'label': 'Bateria', 'key': 'battery_nombre'},
                ],
            },
        ],
    },
}

_PROVINCIAS = {
    'comunitat valenciana': 'Valencia / Alicante / Castellon',
    'murcia': 'Murcia',
}


def available():
    return [
        {'key': key, 'nombre': entry['nombre']}
        for key, entry in sorted(CATALOG.items())
    ]


def resolve(ccaa):
    return CATALOG.get(_norm(ccaa))


def provincia_hint(ccaa):
    return _PROVINCIAS.get(_norm(ccaa))

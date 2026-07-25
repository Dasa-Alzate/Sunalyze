DEFAULT_KEY = '_default'


def _l(href, text):
    return f'<a href="{href}" class="assist-link">{text}</a>'

TUTORIALS = {
    'resumen': {
        DEFAULT_KEY: {
            'title': 'Panel de resumen',
            'intro': 'Estás en el panel general: los indicadores de tus proyectos y accesos rápidos.',
            'steps': [
                ('Revisa los indicadores', 'Muestran tus proyectos activos, los kWp totales y las memorias generadas.'),
                ('Proyectos recientes', 'Haz clic en cualquier proyecto para retomar su diseño.'),
                ('Crea un proyecto', f'Usa {_l("/app/diseno", "«Nuevo proyecto»")} para empezar de coordenadas a memoria en minutos.'),
            ],
            'tips': ['Con Cmd/Ctrl+K abres la paleta de comandos desde cualquier vista.'],
        },
    },
    'proyectos': {
        DEFAULT_KEY: {
            'title': 'Listado de proyectos',
            'intro': 'Aquí gestionas todos los proyectos de tu organización.',
            'steps': [
                ('Busca y filtra', 'Usa la barra de búsqueda (cliente o dirección) y el filtro por estado del flujo de legalización.'),
                ('Abre un proyecto', 'Haz clic en una fila para entrar a su diseño.'),
                ('Duplica o elimina', 'Los iconos al final de cada fila duplican o mandan el proyecto a la papelera.'),
            ],
            'tips': [f'El número de serie (ej. DEMO-0001) se configura en {_l("/app/configuracion", "Configuración → Marca")}.'],
        },
    },
    'diseno': {
        DEFAULT_KEY: {
            'title': 'Asistente de diseño',
            'intro': 'El asistente te lleva de los datos del lugar a la memoria técnica en cinco pasos.',
            'steps': [
                ('Completa cada paso', 'Los pasos bloqueados se desbloquean al completar los datos obligatorios del paso anterior.'),
                ('Guarda tu avance', 'El botón «Guardar» persiste el proyecto en cualquier momento.'),
            ],
            'tips': ['El resumen lateral se actualiza en vivo con cada cálculo.'],
        },
        'lugar': {
            'title': 'Paso 1 — Datos del lugar',
            'intro': 'Define cliente, consumo y ubicación de la instalación.',
            'steps': [
                ('Nombre del cliente', 'Obligatorio: identifica el proyecto en el listado.'),
                ('Necesidad anual', 'El consumo anual en kWh; lo encuentras en la factura eléctrica.'),
                ('Ubica la instalación', 'Busca la dirección o haz clic directamente en el mapa para fijar el pin.'),
                ('Instalación coplanar', 'Márcala si los paneles siguen la pendiente del tejado; define inclinación y azimut (180 = sur).'),
            ],
            'tips': ['Si la dirección exacta no aparece, busca la localidad y ajusta el pin a mano.'],
        },
        'equipos': {
            'title': 'Paso 2 — Selección de equipos',
            'intro': 'Elige panel, inversor y batería desde tu biblioteca.',
            'steps': [
                ('Panel solar', f'Obligatorio para dimensionar; busca por nombre o potencia. ¿No aparece? Añádelo en {_l("/app/equipos", "Equipos")}.'),
                ('Inversor', 'Opcional: si no eliges, el análisis propone inversores compatibles.'),
                ('Batería', 'Opcional: al elegirla define también la cantidad.'),
            ],
            'tips': [f'¿No encuentras un equipo? Añádelo en {_l("/app/equipos", "la vista Equipos")} o impórtalo desde {_l("/app/equipos?tab=marketplace", "el marketplace")}.'],
        },
        'analisis': {
            'title': 'Paso 3 — Análisis y dimensionamiento',
            'intro': 'Calcula strings, producción estimada y cobertura del consumo.',
            'steps': [
                ('Calcula', 'Pulsa «Calcular dimensionamiento» para obtener el diseño eléctrico.'),
                ('Revisa los resultados', 'Strings, paneles por string y producción anual estimada con datos PVGIS.'),
                ('Recalcula si cambias algo', 'Si un dato queda obsoleto verás el aviso de «desactualizado».'),
            ],
            'tips': ['El aviso amarillo en la lista de pasos indica que los resultados quedaron desactualizados.'],
        },
        'diagrama': {
            'title': 'Paso 4 — Diagrama unifilar',
            'intro': 'Genera el esquema unifilar de la instalación como plano eléctrico.',
            'steps': [
                ('Elige plantilla', 'Solar con/sin fusibles, con baterías, CC por strings, conexión a red o sistema completo.'),
                ('Ajusta parámetros', 'Los campos vienen pre-rellenados con tu panel e inversor del paso 2.'),
                ('Descarga el plano', 'El botón de descarga guarda el esquema como imagen para adjuntarlo donde necesites.'),
            ],
            'tips': ['Estos esquemas se incrustan automáticamente en la memoria técnica.'],
        },
        'memoria': {
            'title': 'Paso 5 — Memoria técnica',
            'intro': 'Último paso: genera la memoria técnica firmable.',
            'steps': [
                ('Ir a la memoria', 'El botón te lleva al editor de memoria con los datos del proyecto precargados.'),
                ('Completa los campos', 'Los campos vacíos se marcan en el documento; complétalos antes de firmar.'),
            ],
            'tips': [],
        },
    },
    'memoria': {
        DEFAULT_KEY: {
            'title': 'Memoria técnica',
            'intro': 'Editor de la memoria técnica: verás el documento crecer en vivo mientras completas los campos.',
            'steps': [
                ('Completa las secciones', 'Cada sección del índice agrupa campos del documento; los vacíos se resaltan.'),
                ('Genera el PDF', 'El botón de generar produce el PDF con esquemas y fichas técnicas anexas.'),
                ('Firma', 'Con la memoria completa puedes firmarla y avanzar el estado del proyecto.'),
            ],
            'tips': ['La memoria incluye los esquemas unifilares como planos con cajetín normativo.'],
        },
    },
    'legalizacion': {
        DEFAULT_KEY: {
            'title': 'Legalización del proyecto',
            'intro': (
                'Desde aquí sigues el expediente de la instalación: estado, guía de tramitación '
                'de tu comunidad autónoma, modelo oficial de MTD y número de expediente de Industria.'
            ),
            'steps': [
                ('Asigna la comunidad autónoma', 'Con la CCAA asignada aparecen la guía paso a paso, los enlaces a la sede y los impresos oficiales. De momento: Comunitat Valenciana y Región de Murcia.'),
                ('Firma la memoria antes de avanzar', 'El flujo exige la memoria técnica firmada para pasar a «En revisión» o «Presentado»; así el expediente siempre referencia un documento concreto.'),
                ('Descarga el modelo oficial de MTD', 'En la Comunitat Valenciana, Sunalyze rellena el impreso oficial de la GVA (modelo 23167) con los datos del proyecto; en Murcia genera un documento con la estructura del modelo IEBT de la CARM.'),
                ('Usa el asistente de presentación', 'Muestra los datos del proyecto en el mismo orden en que los pide el formulario de la sede electrónica, con botón de copiar campo a campo.'),
                ('Registra el expediente', 'Al presentar, la sede te devuelve un justificante con número de expediente: guárdalo aquí para que quede en el historial del proyecto.'),
            ],
            'tips': [
                'El proceso legal completo es: memoria técnica (MTD) → código CAU y permiso de acceso con la distribuidora → ejecución → certificado de instalación (CIE) → presentación telemática en la sede de Industria de tu CCAA → inscripción en el registro de autoconsumo → compensación de excedentes con tu comercializadora.',
                'La presentación en la sede es siempre tuya: exige tu certificado digital de instalador habilitado y no puede delegarse en ningún software. Sunalyze prepara los documentos y los datos; tú firmas y presentas.',
                f'Comunitat Valenciana: trámite de autoconsumo ≤10 kW en {_l("https://www.gva.es/es/inicio/procedimientos?id_proc=18168", "el procedimiento PROP 18168")} y de BT con MTD en {_l("https://sede.gva.es/es/detall-tramit?id_proc=440", "el PROP 440")}.',
                f'Región de Murcia: registro de instalaciones de BT por declaración responsable en {_l("https://sede.carm.es/web/pagina?IDCONTENIDO=19&IDTIPO=240", "el procedimiento 0019 de la sede de la CARM")}; la tasa se paga durante la presentación.',
                'Normativa de referencia: RD 244/2019 (autoconsumo) y REBT RD 842/2002 con la ITC-BT-40 (instalaciones generadoras). Con potencia ≤10 kW basta la MTD; por encima hace falta proyecto técnico.',
            ],
        },
    },
    'equipos': {
        DEFAULT_KEY: {
            'title': 'Biblioteca de equipos',
            'intro': 'Gestiona paneles, inversores, baterías y cables de tu organización.',
            'steps': [
                ('Navega por pestañas', 'Cada tipo de equipo tiene su pestaña con contador.'),
                ('Añade o importa', 'Alta manual con «Añadir» o masiva con «Importar» (TSV/CSV/Excel).'),
                ('Edita cualquier equipo', 'Los equipos traídos automáticamente de la web llevan la etiqueta «Scraped»; desaparece al editarlos a mano.'),
            ],
            'tips': [f'La etiqueta con el nombre del catálogo puede llevar color: elígelo en {_l("/app/equipos?tab=marketplace", "el marketplace")}.'],
        },
        'marketplace': {
            'title': 'Marketplace de catálogos',
            'intro': 'Suscríbete a catálogos oficiales o gestiona los tuyos.',
            'steps': [
                ('Suscríbete', '«Añadir a mi biblioteca» hace visibles los equipos del catálogo en tus pestañas.'),
                ('Crea catálogos propios', 'Agrupa tus equipos por proveedor o proyecto.'),
                ('Color del catálogo', 'El selector de color de cada tarjeta tiñe la etiqueta del catálogo en los listados de equipos.'),
            ],
            'tips': [],
        },
    },
    'modulos': {
        DEFAULT_KEY: {
            'title': 'Módulos',
            'intro': 'Activa o desactiva módulos opcionales de la plataforma para tu organización.',
            'steps': [
                ('Explora los módulos', 'Plantillas, finanzas y posventa amplían el flujo base.'),
                ('Instala', 'Al activar un módulo aparece su entrada en la barra lateral.'),
            ],
            'tips': [],
        },
    },
    'plantillas': {
        DEFAULT_KEY: {
            'title': 'Plantillas de documentos',
            'intro': 'Crea y edita plantillas de documentos (certificados, contratos…) con variables.',
            'steps': [
                ('Filtra por tipo', 'Los botones de filtro sobre la galería la acotan por tipo de documento.'),
                ('Edita en el builder', 'Cada plantilla se edita con variables «{{ }}» que se rellenan con datos del proyecto.'),
            ],
            'tips': [],
        },
    },
    'finanzas': {
        DEFAULT_KEY: {
            'title': 'Análisis financiero',
            'intro': 'Modela la rentabilidad del proyecto: inversión, ahorro y retorno.',
            'steps': [
                ('Elige el proyecto', f'Los escenarios financieros se asocian a un proyecto aprobado o en curso; ábrelo desde {_l("/app/proyectos", "Proyectos")}.'),
                ('Ajusta supuestos', 'Precio de la energía, subida anual, degradación de paneles.'),
                ('Lee los resultados', 'Payback, TIR y ahorro acumulado a 25 años.'),
            ],
            'tips': [],
        },
    },
    'posventa': {
        DEFAULT_KEY: {
            'title': 'Posventa',
            'intro': 'Seguimiento de instalaciones entregadas: incidencias y mantenimiento.',
            'steps': [
                ('Registra la instalación', f'Vincula la instalación real al proyecto aprobado; lo encuentras en {_l("/app/proyectos", "Proyectos")}.'),
                ('Gestiona incidencias', 'Registra las incidencias y ciérralas al resolverlas.'),
            ],
            'tips': [],
        },
    },
    'actividad': {
        DEFAULT_KEY: {
            'title': 'Actividad',
            'intro': 'Bitácora de acciones de tu organización, con código de colores por tipo.',
            'steps': [
                ('Lee la línea de tiempo', 'Verde = crear, amarillo = editar, rojo = borrar, azul = renombrar.'),
                ('Salta al elemento', 'La flecha de cada evento te lleva al recurso afectado.'),
            ],
            'tips': [],
        },
    },
    'papelera': {
        DEFAULT_KEY: {
            'title': 'Papelera',
            'intro': 'Elementos borrados que aún puedes restaurar.',
            'steps': [
                ('Restaura', 'El botón de restaurar devuelve el elemento a su vista original.'),
            ],
            'tips': ['También puedes deshacer un borrado reciente con Cmd/Ctrl+Z.'],
        },
    },
    'configuracion': {
        DEFAULT_KEY: {
            'title': 'Configuración',
            'intro': 'Ajustes de la organización: marca y flags de plataforma.',
            'steps': [
                ('Marca', 'Nombre, logo y prefijo del número de serie de proyectos.'),
                ('Flags', 'Solo superadmin: activa características por organización o usuario.'),
            ],
            'tips': [],
        },
    },
    'equipo': {
        DEFAULT_KEY: {
            'title': 'Equipo',
            'intro': 'Miembros de tu organización, roles e invitaciones.',
            'steps': [
                ('Invita', 'Envía invitaciones por email con un rol asignado.'),
                ('Cambia roles', 'Owner ⊇ admin ⊇ member: cada rol hereda los permisos del inferior.'),
            ],
            'tips': [],
        },
    },
}

GENERIC = {
    'title': 'Sunalyze',
    'intro': 'Navega con la barra lateral o abre la paleta de comandos con Cmd/Ctrl+K.',
    'steps': [
        ('Proyectos', f'El flujo principal: de coordenadas a memoria técnica firmable. Empieza en {_l("/app/proyectos", "Proyectos")}.'),
        ('Equipos', f'Tu biblioteca de paneles, inversores, baterías y cables: {_l("/app/equipos", "ábrela aquí")}.'),
    ],
    'tips': [],
}


class HelpService:

    @staticmethod
    def tutorial(view, subview=None):
        section = TUTORIALS.get(view)
        if not section:
            return GENERIC
        if subview and subview in section:
            return section[subview]
        return section.get(DEFAULT_KEY, GENERIC)

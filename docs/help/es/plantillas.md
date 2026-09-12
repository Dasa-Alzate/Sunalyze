---
title: Plantillas de documentos
routes:
  - plantillas
order: 65
keywords: [plantillas, documentos, memoria, propuesta, variables, builder, biblioteca]
---

# Concepto

Las plantillas permiten crear y reutilizar documentos estructurados — memorias de cálculo, propuestas comerciales, documentos legales y análisis de caso — con variables que se rellenan automáticamente con los datos reales de cada proyecto.

:::callout{tone=brand}
Esta sección está disponible solo si el flag **templates** está habilitado en tu organización. Contacta con el administrador si no ves la opción en el menú.
:::

:::cards
- **Banco** — plantillas compartidas por toda la organización, creadas por tus compañeros o importadas.
- **Mis plantillas** — plantillas que has creado tú directamente.
- **Biblioteca** — selección de plantillas instaladas en tu espacio de trabajo, con etiquetas y favoritos para organizarlas.
:::

## Tipos de documento

Cada plantilla tiene un tipo: **Memoria de cálculo**, **Documento legal**, **Propuesta comercial** o **Análisis de caso**. El tipo determina qué variables de proyecto están disponibles en el editor.

## Estados de una plantilla

Una plantilla pasa por tres estados: **Borrador** (editable, no visible para clientes), **Publicada** (lista para generar documentos) y **Archivada** (retirada del uso activo).

# Tutorial

## Crear una plantilla nueva

:::steps
1. Ve a **Plantillas** — URL `/app/plantillas`.
2. Pulsa **Nueva plantilla** en la barra superior.
3. Rellena el nombre, el tipo de documento y la descripción en el diálogo y confirma.
4. Se abre el editor de la plantilla. Usa **Añadir sección** para incorporar bloques de texto.
5. En cada sección, escribe el cuerpo y pulsa **Insertar variable** para añadir expresiones `{{ variable }}` con datos del proyecto.
6. Pulsa **Guardar** para conservar el borrador o **Publicar** para dejarlo listo para uso.
:::

## Filtrar y organizar la biblioteca

:::steps
1. Cambia a la pestaña **Biblioteca** para ver las plantillas instaladas en tu espacio.
2. Usa los filtros **Etapa** y **País** para acotar la búsqueda; activa **Favoritos** para ver solo las marcadas con estrella.
3. Pulsa **Organizar** en una tarjeta para asignarle categorías y etiquetas.
4. Pulsa **Quitar de la selección** si ya no necesitas esa plantilla en la biblioteca.
:::

:::tip{tone=info title="Plantillas oficiales"}
Las plantillas marcadas con el distintivo **Oficial** son del sistema: puedes usarlas y asignarlas a proyectos, pero no editarlas. Duplícalas si necesitas personalizarlas.
:::

## Instalar una plantilla del banco

:::steps
1. En la pestaña **Banco** o **Mis plantillas**, localiza la tarjeta que te interesa.
2. Pulsa **Instalar**: la plantilla pasa a tu **Biblioteca**.
3. Desde la Biblioteca puedes marcarla como favorita o asignarle etiquetas.
:::

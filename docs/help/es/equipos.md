---
title: Biblioteca de equipos
routes:
  - equipos
  - equipos/panels
  - equipos/inverters
  - equipos/batteries
  - equipos/wires
  - equipos/marketplace
order: 50
keywords: [equipos, paneles, inversores, baterias, cables, catalogo, marketplace, importar]
---

# Concepto

La Biblioteca de equipos centraliza todos los equipos disponibles en tu workspace: paneles fotovoltaicos, inversores, baterías y cables. Los equipos se agrupan en **catálogos**; puedes tener catálogos propios y suscribirte a catálogos compartidos desde el **Marketplace**.

## Las cinco pestañas

:::cards
- **Paneles** — módulos fotovoltaicos con Voc, Vmp, Imp, dimensiones y precio tarifa.
- **Inversores** — inversores con potencia AC/DC, Vmax, corrientes máximas de entrada y salida.
- **Baterías** — acumuladores con capacidad nominal, capacidad útil, potencia, voltaje y tecnología.
- **Cables** — secciones con tipo, material (Cu/Al), sección en mm², corriente máxima y número de conductores.
- **Marketplace** — catálogos oficiales y de terceros que puedes añadir o quitar de tu biblioteca con un clic.
:::

## Catálogos propios y del Marketplace

Cada equipo pertenece a un catálogo. Los catálogos propios (icono de usuario) son editables; los del marketplace (icono de tienda) son de solo lectura y se identifican con el candado en la columna de acciones. Los equipos importados automáticamente desde fuentes externas llevan la etiqueta **Scraped**.

# Tutorial

## Añadir un equipo manualmente

:::steps
1. Abre la pestaña correspondiente (ej. **Paneles**).
2. Pulsa **Añadir panel** en la esquina superior derecha.
3. Rellena los campos obligatorios: **Nombre**, **Potencia (W)**, **Voc (V)**, **Vmp (V)**, **Imp (A)**.
4. Completa los opcionales que tengas (dimensiones, precio, ficha técnica…).
5. Si tienes varios catálogos propios, elige el **Catálogo** destino en el desplegable superior del cajón.
6. Pulsa **Guardar**. El equipo aparece inmediatamente en la tabla.
:::

## Importar equipos en lote

:::steps
1. En la pestaña deseada, pulsa **Importar**.
2. Descarga la **plantilla TSV** con el botón correspondiente y rellena una fila por equipo.
3. Arrastra el fichero a la zona de carga o haz clic para buscarlo (TSV, CSV o Excel, máx. 2 MB).
4. Al finalizar verás el resumen: equipos creados, actualizados y, si los hay, filas con error.
:::

:::tip{tone=info title="Catálogo automático"}
Si aún no tienes ningún catálogo propio, el primer equipo que añadas o importes se guarda en «Mis equipos», que se crea automáticamente.
:::

## Suscribirse a un catálogo del Marketplace

:::steps
1. Ve a la pestaña **Marketplace**.
2. Localiza el catálogo que te interesa — los catálogos oficiales llevan la etiqueta **Oficial**.
3. Pulsa **Añadir a mi biblioteca**. Los equipos quedan disponibles de inmediato en las pestañas de paneles, inversores, etc.
4. Para quitarlo, vuelve al Marketplace y pulsa **En tu biblioteca · Quitar**.
:::

## Exportar la biblioteca

En cualquier pestaña (excepto Marketplace) usa el botón **Exportar** para descargar la vista actual en CSV o Excel. Puedes filtrar previamente por catálogo con el desplegable **Todos los catálogos** para exportar solo un subconjunto.

:::callout{tone=warning}
Los equipos del marketplace no se pueden editar ni eliminar desde la biblioteca. Para modificarlos debes duplicar el equipo a un catálogo propio o contactar con el propietario del catálogo.
:::

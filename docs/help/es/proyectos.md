---
title: Proyectos
routes:
  - proyectos
order: 20
keywords: [proyectos, lista, estados, filtros, duplicar, exportar, papelera]
---

# Concepto

La vista de Proyectos es el listado completo de todos los diseños de tu workspace. Desde aquí puedes buscar, filtrar por estado, duplicar o eliminar proyectos, y exportar los datos a CSV o Excel.

## Columnas de la tabla

Cada fila representa un proyecto e incluye: **Cliente / Dirección**, **Panel** (modelo y número de unidades), **kWp**, **Estado** y **Modificado** (tiempo relativo desde la última edición).

## Estados de un proyecto

:::cards
- **Borrador** — diseño en progreso, aún sin equipos confirmados.
- **Análisis** — equipos seleccionados, producción calculada.
- **Disposición** — módulos colocados en la cubierta.
- **Memoria** — memoria técnica generada y lista para firmar.
:::

# Tutorial

## Buscar y filtrar

:::steps
1. Escribe en el campo **Buscar cliente o dirección…** para filtrar por nombre de cliente o dirección al instante.
2. Usa el desplegable **Todos los estados** para acotar a un estado concreto.
3. Si ningún proyecto coincide, aparece el botón **Limpiar filtros** para restablecer la vista completa.
:::

## Crear, duplicar y eliminar

:::steps
1. Pulsa **Nuevo proyecto** en la barra superior para abrir el asistente de diseño desde cero.
2. En cualquier fila, haz clic en el icono de copiar para **Duplicar** ese proyecto — se crea una copia inmediata con todos sus datos.
3. Haz clic en el icono de papelera para **Eliminar** — el sistema pide confirmación y el proyecto pasa a la papelera (recuperable desde la sección «Papelera»).
:::

:::tip{tone=info title="Deshacer una eliminación"}
Tras eliminar aparece un aviso con el botón **Deshacer** durante unos segundos. Pulsa ahí para restaurar el proyecto sin tener que ir a la papelera.
:::

## Exportar

:::steps
1. Pulsa **Exportar** en la barra de herramientas.
2. Elige el formato (CSV o Excel). Se descarga el listado filtrado en ese momento con las columnas: Cliente, Dirección, Panel, kWp, Estado y Modificado.
:::

## Paginar

Cuando hay más de diez proyectos, aparece la barra de paginación al pie de la tabla. Usa **Anterior** y **Siguiente** o el indicador de página para moverte entre páginas de diez registros.

:::tip{tone=brand title="Atajo de teclado"}
Con el ratón encima de una fila, pulsa **Cmd + D** (Mac) o **Ctrl + D** (Windows) para duplicar ese proyecto sin usar el ratón.
:::

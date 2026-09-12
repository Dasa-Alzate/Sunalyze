---
title: Memoria técnica del proyecto
routes:
  - diseno/memoria
order: 35
keywords: [memoria, pdf, tecnica, legalización, presupuesto, catastral, cups, protecciones]
---

# Concepto

La memoria técnica es el documento oficial que acompaña a la instalación: incluye los datos del cliente, el contrato eléctrico, la configuración del sistema, las protecciones y el presupuesto. Sunalyze la genera como PDF a partir de los datos del proyecto más los campos adicionales que completas en esta pantalla.

La vista se divide en dos columnas: a la izquierda el formulario en acordeón y a la derecha una **Vista previa del documento** que se actualiza en vivo mientras escribes.

## Secciones del formulario

:::cards
- **Cliente y emplazamiento** — nombre, localidad, dirección, código postal y referencia catastral.
- **Contrato eléctrico** — compañía, CUPS, potencia contratada, tensión, tipo de voltaje y objetivo del sistema (con o sin inyección de excedentes).
- **Configuración** — potencia pico, nº de paneles, entradas MPPT, ubicación de paneles, disposición e ubicación del inversor.
- **Protecciones** — magnetotérmico DC, magnetotérmico AC, diferencial AC, protector de sobretensiones y longitud del cable de tierra.
- **Presupuesto** — líneas de presupuesto editables (solo disponible desde un proyecto guardado).
:::

# Criterio

## Campos obligatorios

Todos los campos de las secciones **Cliente y emplazamiento**, **Contrato eléctrico**, **Configuración** y **Protecciones** son obligatorios para generar el PDF. Cada sección muestra un indicador de estado: verde cuando todos sus obligatorios están completos, naranja si faltan algunos.

Si pulsas **Generar PDF** con campos incompletos, la app señala cuántos faltan y abre la primera sección pendiente.

:::callout{tone=warning}
El botón **Generar PDF** está disponible solo para los roles con permiso `memoria:sign`. Si aparece desactivado, contacta con el administrador de tu cuenta.
:::

# Tutorial

## Generar la memoria técnica

:::steps
1. Desde el wizard de diseño, pulsa **Ir a la memoria** en la barra superior o en el último paso del asistente.
2. Comprueba que los datos de **Cliente y emplazamiento** son correctos; muchos vienen pre-rellenados del paso **Datos del lugar**.
3. Rellena el **Contrato eléctrico**: compañía distribuidora, CUPS, potencia contratada y tipo de voltaje.
4. Revisa **Configuración**: potencia pico y nº de paneles llegan del análisis; ajusta la disposición y la ubicación del inversor según el caso real.
5. Rellena **Protecciones** con los valores de los elementos de protección elegidos.
6. Pulsa **Guardar** para persistir los datos en el proyecto.
7. Pulsa **Generar PDF** — se abre el documento en una pestaña nueva listo para firmar y adjuntar.
:::

:::tip{tone=info title="Presupuesto"}
Si el proyecto está guardado, aparece la sección **Presupuesto** al final del acordeón. Añade líneas con material, instalación y otros conceptos; se incluyen automáticamente en el PDF.
:::

:::tip{tone=brand}
Desde esta misma pantalla puedes ir a **Legalización** con el botón de la barra superior para tramitar el expediente de la instalación una vez firmada la memoria.
:::

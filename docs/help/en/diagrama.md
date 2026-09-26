---
source_hash: 6947153a81f5
title: Single-line diagram
routes:
  - diseno/diagrama
order: 34
keywords: [diagram, single-line, schematic, fuses, battery, single-phase, three-phase, svg]
---

# Concepto

The **Diagram** step generates the single-line schematic of the installation from the template, the project equipment and the electrical parameters you adjust in the side panel. The result is a downloadable vector SVG ready to attach to the technical report or the legalisation dossier.

The diagram updates live as you type: no regenerate button is needed.

:::callout{tone=info}
The single-line diagram requires the sizing to have been calculated first. If you access the step without analysis results, a shortcut to the **Analysis** step is shown.
:::

## Templates

:::cards
- **Solar con fusibles** — DC strings with string fuses, DC switch, inverter and AC protections. The default template.
- **Solar sin fusibles** — same but without string fuses; valid for single-string installations.
- **Solar con baterías** — includes the battery block and the energy management system.
:::

Use the **Con fusibles de cadena** and **Con baterías** checkboxes to toggle without manually changing the template.

# Tutorial

## Generating and downloading the schematic

:::steps
1. Go to the **Diagram** step; the template is pre-selected based on the project equipment (with or without battery).
2. Select a different **Plantilla** from the dropdown if needed.
3. Adjust the **Campo fotovoltaico (CC)** parameters: **Modelo de panel**, **Voc del panel**, **Isc del panel**, **Paneles por cadena**, **Nº de cadenas**, **Fusible CC**, **Tensión del seccionador CC** and **Sección de cable CC**.
4. Adjust the **Salida e inversor (CA)** parameters: **Modelo de inversor**, **Potencia del inversor**, **Corriente de salida**, **Fases** (Monofásico / Trifásico), **Magnetotérmico**, **Diferencial**, **Sensibilidad diferencial** and **Sección de cable CA**.
5. Review the **Vista previa en vivo** on the right: it updates with every change.
6. Click **Descargar SVG** to save the vector schematic.
:::

:::tip{tone=success}
The **Modelo de panel**, **Voc**, **Isc**, **Modelo de inversor** and **Potencia del inversor** fields are pre-filled with data from the project's linked equipment. You can overwrite them if you need to adjust any value for the schematic.
:::

:::tip{tone=info title="From any step"}
The **Diagrama unifilar** button in the top bar opens this step directly without going through the previous ones, useful when you only want to adjust or download the schematic.
:::

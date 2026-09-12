---
source_hash: 363fc920f316
title: Project technical report
routes:
  - diseno/memoria
order: 35
keywords: [report, pdf, technical, legalisation, budget, cadastral, cups, protections]
---

# Concepto

The technical report is the official document that accompanies the installation: it includes client data, the electricity contract, the system configuration, protections and the budget. Sunalyze generates it as a PDF from the project data plus the additional fields you complete on this screen.

The view is split into two columns: on the left the accordion form and on the right a **Vista previa del documento** that updates live as you type.

## Form sections

:::cards
- **Cliente y emplazamiento** — name, location, address, postcode and cadastral reference.
- **Contrato eléctrico** — utility company, CUPS, contracted power, voltage, voltage type and system objective (with or without grid export).
- **Configuración** — peak power, number of panels, MPPT inputs, panel location, layout and inverter location.
- **Protecciones** — DC circuit breaker, AC circuit breaker, AC RCD, surge protector and earth cable length.
- **Presupuesto** — editable budget lines (only available from a saved project).
:::

# Criterio

## Mandatory fields

All fields in the **Cliente y emplazamiento**, **Contrato eléctrico**, **Configuración** and **Protecciones** sections are mandatory to generate the PDF. Each section shows a status indicator: green when all its mandatory fields are complete, amber if some are missing.

If you click **Generar PDF** with incomplete fields, the app shows how many are missing and opens the first pending section.

:::callout{tone=warning}
The **Generar PDF** button is available only for roles with the `memoria:sign` permission. If it appears disabled, contact your account administrator.
:::

# Tutorial

## Generating the technical report

:::steps
1. From the design wizard, click **Ir a la memoria** in the top bar or in the last step of the wizard.
2. Check that the **Cliente y emplazamiento** data are correct; most fields are pre-filled from the **Location** step.
3. Fill in the **Contrato eléctrico**: utility company, CUPS, contracted power and voltage type.
4. Review **Configuración**: peak power and number of panels come from the analysis; adjust the layout and inverter location for the actual installation.
5. Fill in **Protecciones** with the values of the chosen protection devices.
6. Click **Guardar** to persist the data in the project.
7. Click **Generar PDF** — the document opens in a new tab ready to sign and attach.
:::

:::tip{tone=info title="Budget"}
If the project is saved, the **Presupuesto** section appears at the bottom of the accordion. Add lines for material, installation and other items; they are automatically included in the PDF.
:::

:::tip{tone=brand}
From this same screen you can go to **Legalización** with the top-bar button to process the installation dossier once the report is signed.
:::

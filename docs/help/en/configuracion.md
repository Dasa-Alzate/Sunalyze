---
source_hash: e0c10c08be2e
title: Studio settings
routes:
  - configuracion
  - configuracion/marca
  - configuracion/presupuesto
  - configuracion/flags
order: 95
keywords: [settings, branding, logo, budget, flags, colour, pricing, organisation]
---

# Concepto

The **Configuración** section groups all organisation-wide settings: the visual identity applied to generated documents, the economic parameters that feed budgets, and the feature flags that control which modules are active.

:::cards
- **Marca** — logo, primary colour, serial number prefix and document footer.
- **Presupuesto** — labour rates, equipment inflation and custom line items.
- **Flags** — module and experimental-feature activation (platform administrators only).
:::

:::tip{tone=info title="Access"}
The **Marca** and **Presupuesto** tabs require the **org:manage** permission. The **Flags** tab is only visible to platform administrators.
:::

# Tutorial

## Branding

:::steps
1. Go to **Configuración** and select the **Marca** tab.
2. Click **Subir logo** (or **Reemplazar logo**) to upload a PNG, JPEG, WebP or SVG up to 2 MB.
3. Choose the **Color principal** with the colour picker or type the hex value in the text field.
4. Enter the **Prefijo de nº de serie** (up to 8 characters) so your projects are numbered as PREFIX-0001.
5. Fill in the **Texto del pie de página** that will appear on generated documents.
6. Click **Guardar marca** to apply the changes.
:::

## Budget

:::steps
1. Select the **Presupuesto** tab.
2. Enter the **Fijo por instalación (€)**: commissioning and management amount added once per project.
3. Enter the **Por módulo instalado (€/ud)**: multiplied by the number of modules in the design.
4. Adjust the **Inflación general de equipos (%)**: covers price fluctuation; it compounds with each equipment's own inflation without appearing as a separate line item.
5. Add custom line items with **Añadir partida**: choose chapter, description, unit, quantity and unit price.
6. Click **Guardar parámetros** when done.
:::

:::callout{tone=info}
Custom line items are included in every pre-generated budget. Rows with no description are ignored on save.
:::

## Flags

:::steps
1. Select the **Flags** tab (visible only to platform administrators).
2. The table shows all feature flags with their default value and the active global override.
3. Enable or disable the global override for each flag as needed.
4. To revert to the default value, clear the flag's override.
:::

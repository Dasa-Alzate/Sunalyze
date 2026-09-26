---
source_hash: c612724fdd6b
title: Analysis and sizing
routes:
  - diseno/analisis
order: 32
keywords: [analysis, sizing, production, self-consumption, pvgis, irradiance, power, panels]
---

# Concepto

The **Analysis** step runs the sizing engine: it takes the site coordinates, the selected panel and the annual need, queries the PVGIS-SARAH3 irradiance database and returns the photovoltaic array required to cover the demand at the specified self-consumption percentage.

The result includes peak array power, number of modules, estimated annual production and, if an inverter is fixed, the string configuration with MPP window verification.

:::tip{tone=info title="PVGIS-SARAH3"}
Irradiance data come from the European PVGIS-SARAH3 database, which covers the Iberian Peninsula, Balearic Islands and Canary Islands at 5 km resolution. The calculation uses the optimal tilt for the latitude (or the coplanar angle if defined in the previous step).
:::

## Key metrics

:::cards
- **Peak array power** — sum of the nominal power of all modules (kWp).
- **Estimated annual production** — energy generated in a typical year (kWh), including system losses.
- **Panels** — number of modules needed to cover the demand at the fixed self-consumption level.
- **Annual irradiance** — solar energy available in the generator plane (kWh/m²).
- **Optimal angle** — tilt of maximum capture for the project latitude (°).
- **Required area** — approximate area occupied by the array (m²), if the panel has dimensions in the catalogue.
:::

# Criterio

## When to recalculate

The analysis is marked as stale (orange triangle in the side summary) every time you change coordinates, annual need, self-consumption, panel or inverter. Click **Recalcular** to update.

You do not need to recalculate if you only change client data, wiring or layout: those fields do not affect sizing.

## Compatible inverters

If no inverter is fixed in **Equipment**, the analysis shows the **Compatible inverters** table with all catalogue models that fit the calculated string MPP window, sorted by voltage margin. Click **Elegir** on your preferred row — the inverter is linked to the project for the subsequent steps.

# Tutorial

## Running the sizing

:::steps
1. Go to the **Analysis** step from the step menu or with the **Continuar** button in **Equipment**.
2. If there is no result yet, click **Calcular dimensionamiento**.
3. Review the metrics: peak power, panels and annual production.
4. If no inverter is fixed, choose one from the **Compatible inverters** table by clicking **Elegir**.
5. If you change anything in earlier steps, click **Recalcular** to refresh the results.
6. Click **Continuar** to move to **Layout**.
:::

:::callout{tone=warning}
If the analysis fails with a network or PVGIS error, check that the coordinates are within the area covered by PVGIS (Europe, Africa and part of Asia). Out-of-range coordinates produce an immediate error.
:::

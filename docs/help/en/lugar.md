---
source_hash: 8d74261462a6
title: Project location
routes:
  - diseno
  - diseno/lugar
order: 30
keywords: [location, coordinates, latitude, longitude, consumption, client, annual need, coplanar]
---

# Concepto

The «Location» step anchors the project to the territory: it establishes who the client is, where the installation is located and how much energy it needs. With those three pieces of data — coordinates, annual consumption and self-consumption percentage — the calculation engine can query actual irradiance from PVGIS and size the photovoltaic array.

## Client data

The **Client** block identifies the project in the list and in the header of the technical report.

:::cards
- **Client / project** — name or company; appears in the topbar and in the PDF. Mandatory field.
- **Location** — municipality; filled automatically when you use the map to fix the coordinates.
- **Address** — street and number; goes directly to the «Client and location» section of the report.
:::

## Site and consumption

:::cards
- **Latitude / Longitude** — decimal coordinates (e.g. 38.352 / −0.493). Mandatory to query PVGIS.
- **Annual need** — consumption you want to cover, in kWh/year. Mandatory for sizing.
- **Self-consumption** — percentage of consumption to cover with solar (70 %, 80 %, 90 % or 100 %).
:::

:::tip{tone=info title="Interactive map"}
If the **geo_map** flag is active on your account, a map appears below the form. Click any point to set latitude and longitude automatically; **Location** is also filled with the nearest place name.
:::

## Coplanar installation

Check **Instalación coplanar (definir inclinación y azimut)** when modules are mounted on a tile roof or fixed-angle surface. When enabled, two additional fields appear:

:::cards
- **Inclinación (°)** — angle of the plane from horizontal (0–90°).
- **Azimut (°)** — orientation of the plane; 180° = true south.
:::

If you do not check coplanar, the analysis step automatically calculates the optimal tilt angle for your latitude.

# Tutorial

## Filling in the location data

:::steps
1. Type the name in **Cliente / proyecto** — it is the only strictly mandatory field to save the project.
2. Fill in **Necesidad anual** (kWh/year) with the client's actual or estimated consumption.
3. Set **Autoconsumo** to the percentage you want to cover with solar.
4. Enter **Latitud** and **Longitud** or use the map to fix the point with a click.
5. If the roof has a fixed tilt, enable **Instalación coplanar** and enter the inclination and azimuth.
6. Click **Continuar** — the wizard validates mandatory fields before moving to the next step.
:::

:::callout{tone=warning}
If you change the coordinates or the annual need after calculating, the side summary shows a «Entradas cambiadas — recalcula para actualizar» warning. Go back to the **Analysis** step and click **Recalcular**.
:::

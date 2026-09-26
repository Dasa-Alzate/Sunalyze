---
source_hash: 8a53db96e25b
title: Module layout
routes:
  - diseno/disposicion
order: 40
keywords: [layout, zones, roof, strings, shadows, heatmap, rows]
---

# Concepto

The layout step translates the analysis sizing into a real placement on the roof: where each module fits, how they are grouped into strings, and how much production you lose to shadows and orientation.

## Zones: one per roof face

Each zone represents a roof face (slope) with its own plane: azimuth, tilt and whether the modules are coplanar or on a raised structure.

:::cards
- **Zona** — roof polygon with its own plane and rows of modules.
- **Exclusiones** — areas where mounting is not possible (skylights, setbacks).
- **Obstáculos** — raised elements that cast shadows (chimneys, antennas).
:::

:::tip{tone=info title="Multi-face roofs"}
Create one zone per face with «Añadir zona». Production is calculated per zone using its real azimuth and tilt, not a single average plane.
:::

# Criterio

## Row spacing

On flat roofs (non-coplanar), the IDAE spacing prevents one row from shading the next at the winter-solstice noon.

:::norm{code="IDAE PCT-C-REV"}
The minimum row distance is calculated with **d = h / tan(61° − latitude)**, where *h* is the obstacle height (the front row itself).
:::

:::callout{tone=warning}
Reducing the spacing below the recommended value gains modules but loses annual production to mutual shading. The options screen quantifies that trade-off before you decide.
:::

## Strings

Modules are grouped into strings by colour. A string must stay within the inverter's MPP window: the sum of module voltages in the cold must not exceed the maximum V, nor fall below the minimum MPP in the heat.

# Flujo

:::flow
- **Draw the roof** — trace the face polygon on the map.
- **Configure the plane** — azimuth, tilt and coplanar/structure.
- **Auto-place** — fill the zone with the recommended spacing.
- **Adjust** — individual cells, exclusions and obstacles.
- **Strings** — group and check against the MPP window.
:::

# Tutorial

## Place the modules

:::steps
1. Click **Dibujar cubierta** and mark the perimeter of the face; close the polygon at the first vertex.
2. Adjust the zone plane: azimuth (180° = south), tilt and coplanar if mounted on tiles.
3. Click **Auto-colocar**: the grid uses the IDAE spacing on flat roofs and 2 cm on coplanar ones.
4. Paint or erase individual cells with the mouse to adapt the shape to reality.
5. Add **obstáculos** with their height: the shadow map recalculates immediately.
:::

:::screenshot{src=diseno/disposicion.png alt="Layout editor with zones and heatmap"}
Editor with two zones, obstacles and the annual shadow map active.
:::

## If the analysis modules don't fit

:::steps
1. When the area is insufficient, **Ver opciones** appears with quantified alternatives.
2. Compare: add another zone, tighten rows (+modules, −production), rotate orientation, increase module power or accept fewer modules.
3. Choosing a more powerful module takes you back to **Equipos** with the minimum wattage already calculated.
:::

:::tip{tone=success}
The analysis production is fed back from what is actually placed: if you change the layout, the analysis step reflects the new per-zone production.
:::

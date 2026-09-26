---
source_hash: 00e3701eadda
title: Project equipment
routes:
  - diseno/equipos
order: 31
keywords: [equipment, panel, inverter, battery, cable, wiring, catalog, selection]
---

# Concepto

The **Equipment** step links catalogue items to the specific project. What you choose here determines the sizing the analysis calculates, the schematic the circuit diagram generates and the datasheets that appear in the technical report.

:::cards
- **Solar panel** — mandatory. Defines the power, voltages and dimensions of each module.
- **Inverter** — optional at this step; leave it blank and the analysis will offer a list of compatible models.
- **Battery** — optional. If included, the analysis calculates the bank, autonomy and annual contribution.
- **Wiring** — optional. Cross-section and material of DC, AC and earth cables; feeds the technical report.
:::

## Equipment search

Each selector is a real-time search field: type part of the name, the power or any other datum and the list filters instantly. Navigate with ↑ ↓ keys and confirm with Enter, or click the row.

:::tip{tone=info title="Without a fixed inverter"}
Leaving **Inversor** blank is the recommended option if you have not yet decided. The analysis calculates the string voltage range and displays a **Compatible inverters** table with their voltage margin — choose directly from there.
:::

# Criterio

## Inverter compatibility

The analysis checks the MPP window: the cold string voltage (Voc × N modules × temperature factor) must not exceed the inverter's **V max**; at operating temperature, the minimum MPP voltage must remain above the lower threshold.

If you fix an inverter that does not comply, the calculation indicates it. You can check **Mostrar todos los inversores compatibles (desactivar filtro por potencia)** to see the full library without filtering by power and choose manually.

## Battery and quantity

When you select a battery, the **Cantidad de baterías** field appears. The analysis multiplies the nominal capacity by that quantity to calculate the total bank and usable energy.

# Tutorial

## Selecting the equipment

:::steps
1. Click the **Panel solar** search box and type the model or power; select the module from the list.
2. If you already know which inverter to use, search for it in **Inversor**; otherwise leave it blank.
3. If the project includes storage, search for the battery in **Batería** and set the **Cantidad de baterías**.
4. In the **Cableado** section, select the cross-section for **Cable CC (serie fotovoltaica)**, **Cable CA (salida del inversor)** and **Cable de tierra** if the technical report requires them.
5. Click **Calcular y continuar** — the wizard launches the sizing and moves to the **Analysis** step.
:::

:::tip{tone=success}
To clear the inverter, battery or cable selection, click the × that appears on the right of the search box when something is selected.
:::

:::callout{tone=info}
If the panel does not appear in the catalogue, go to **Equipos › Paneles** in the sidebar to add it before returning to the design.
:::

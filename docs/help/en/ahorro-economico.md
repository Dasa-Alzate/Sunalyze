---
source_hash: a99dd634368d
title: Economic analysis and battery selection
routes:
  - diseno/economico
order: 34
keywords: [savings, bill, economics, plan, retailer, tariff, payback, battery, profitability, self-consumption, solstice, charts]
---

# Concepto

The **Economic analysis** step crosses the customer's consumption profile with solar production **hour by hour over a full year** and translates the result into euros using the customer's **electricity plan**: today's bill, the bill with the system, and what each piece of equipment contributes.

The difference from classic sizing is one figure: **real self-consumption**. It stops being the percentage you declare in step 1 and becomes a computed result — the fraction of consumption that actually coincides (or is stored) with *this* customer's sun hours.

:::cards
- **Bill without panels** — what the customer pays today on their electricity plan. It is also the theoretical savings ceiling.
- **Bill with the system** — same plan, subtracting self-consumption, battery and surplus compensation month by month.
- **Battery contribution** — the real annual bill difference between the system with and without it. A single figure, taxes included.
:::

:::callout{tone=info}
Surplus compensation follows the real rule: it discounts at most down to a zero bill for the month, and the remainder carries over but is never paid out. If you see the warning about surplus that cannot be discounted, there is room for more battery or a smaller array.
:::

# Criterio

The step has two blocks: **Economic savings**, which describes the bill with the chosen plan, and **Battery selection**, which compares alternatives.

## Electricity plan — which prices?

Pick the customer's retailer plan in the selector. Plans are created and edited in **Equipos › Planes eléctricos** (peak, standard, off-peak, surplus, capacity, taxes and meter rental prices). Without a plan, your organisation's reference 2.0TD tariff is used.

## Monthly bill — what will the customer see?

Bars for the bill month by month, before and after, and below them the **summary table** with every month and the annual total: without panels, with the system and savings.

## Typical day — why a battery?

Consumption and production on the **winter solstice (21 December) and summer solstice (21 June)**, the two extremes of daylight in the year. The gap between the consumption curve and the solar bell is exactly what the battery can shift. If both curves already overlap a lot, the battery adds little.

## Battery selection

- **PV power versus savings** — annual savings by array kWp, one curve per battery. Look for the **knee**: where the curve flattens, each extra kWp adds little. The dashed line is the maximum saving (the current bill).
- **Payback versus savings** — each battery is a point: the higher and further left, the more it saves and the sooner it pays back.
- **Profitability by battery** — the table compares bill, savings, contribution and payback for each battery with the current array.

:::callout{tone=warning}
Batteries without a unit price in the catalogue have no payback and are left out of the chart (listed below it). Add prices in the Equipment library and compare again.
:::

# Tutorial

## Calculate and decide

:::steps
1. Link a **consumption profile** in the «Datos del lugar» step and run the sizing.
2. In **Análisis económico**, choose the **Plan eléctrico del cliente**.
3. Click **Calcular ahorro** — the project saves itself and within seconds the KPIs, the monthly bill and the battery selection appear.
4. In **Selección de batería**, decide the power with the first chart and the battery with the payback chart and the profitability table.
5. Show the **Factura mensual** to the customer and use **Día tipo** to explain why the battery matters.
6. If you change plan, equipment or consumption, click **Recalcular**.
:::

:::tip{tone=info title="Public holidays"}
Public holidays are not modelled in the tariff periods yet: they count as working days.
:::

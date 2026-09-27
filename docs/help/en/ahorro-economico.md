---
source_hash: f88b3635e81f
title: Economic savings and decision charts
order: 34
keywords: [savings, bill, economics, sweep, profitability, payback, investment, battery, tariff, self-consumption, charts]
---

# Concepto

The **Economic savings** block in the Analysis step crosses the customer's consumption profile with solar production **hour by hour over a full year** and translates the result into euros: today's bill, the bill with the system, and what each piece of equipment contributes.

The difference from classic sizing is one figure: **real self-consumption**. It stops being the percentage you declare in step 1 and becomes a computed result — the fraction of consumption that actually coincides (or is stored) with *this* customer's sun hours.

:::cards
- **Bill without panels** — what the customer pays today with your organization's tariff (2.0TD by default). Also the theoretical savings ceiling.
- **Bill with the system** — same tariff, subtracting self-consumption, battery and surplus compensation month by month.
- **Battery contribution** — the real difference in annual bill between the system with and without it. One figure, taxes included.
:::

:::callout{tone=info}
Surplus compensation follows the real rule: it discounts at most down to a zero monthly bill, and the leftover carries over but is never paid out. If you see the notice about surpluses that never get discounted, there is room for more battery or less field.
:::

# Criterio

Each tab of the block answers one specific decision. Read them like this:

## Sweep — how many kWp?

Annual savings versus field power, one curve per battery. Look for the **elbow**: where the curve flattens, each extra kWp adds little. The dashed line is the **maximum savings** (the current bill): getting close to it with slack usually means oversizing.

## Profitability — where is the sweet spot?

Annual savings versus **estimated initial investment** (project equipment at catalog prices + your organization's labor). The diagonals mark 3, 5 and 8-year paybacks: the further up-left a point sits, the better. The table below compares batteries with the current field.

:::callout{tone=warning}
Batteries without a unit price in the catalog are left out of this chart (they are listed below): estimating an investment with incomplete prices would produce false paybacks. Set prices in the Equipment library and recalculate.
:::

## Monthly bill — what will the customer see?

Bars of the month-by-month bill, before and after. The sales argument in one image: summer almost disappears, winter drops less.

## Typical day — why a battery?

Consumption and production of an average winter day and summer day. The gap between the consumption curve and the solar bell is exactly what the battery can shift. If the two curves already overlap heavily, a battery adds little.

# Tutorial

## Compute and decide

:::steps
1. Attach a **consumption profile** in the «Site data» step and compute the sizing in **Analysis**.
2. Press **Calcular ahorro** — the project saves itself and within seconds the KPIs and tabs appear.
3. In **Barrido**, decide the power: stay near the curve's elbow.
4. In **Rentabilidad**, pick the battery comparing payback and savings; the «Mayor ahorro» badge marks the winner in euros, but a much shorter payback can weigh more.
5. Show **Factura mensual** to the customer and use **Día tipo** to explain the why of the battery.
6. If you change equipment or consumption, press **Recalcular**.
:::

:::tip{tone=info title="The tariff belongs to your organization"}
Energy prices (peak/flat/off-peak), surplus, power and taxes are configured per organization via the tariff API; a reasonable peninsular 2.0TD is used by default. Holidays are not modeled yet (they count as weekdays).
:::

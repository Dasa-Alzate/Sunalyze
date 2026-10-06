---
source_hash: d20001da6a49
title: Customer consumption profile
order: 33
keywords: [profile, consumption, load curve, hourly, datadis, csv, battery, self-consumption, bill, off-peak, peak]
---

# Concepto

The consumption profile describes **how the customer's electricity use is distributed across the year**, hour by hour. It is not how much they consume (the project's annual consumption says that), but *when*: whether the home spends at night, whether the office only lives Monday to Friday, whether irrigation spikes in summer.

That temporal dimension is what makes real savings computable: midday solar production is only worth what the customer consumes (or stores) at that moment.

:::cards
- **Shape** — the normalized hourly distribution of consumption. This is what the profile stores.
- **Scale** — the project's annual kWh. Defined on the project, not on the profile.
- **Curated profile** — a typical shape ready to use (residential, office, retail, industrial…).
:::

:::tip{tone=info title="Battery value depends on the profile"}
Without a profile, a battery has no computable value: its benefit is exactly the mismatch between when the sun produces and when the customer consumes. With a profile, the system can quantify every kWh shifted from production hours to peak consumption hours.
:::

# Criterio

## Which sample to provide

The more real the sample, the sharper the numbers:

:::cards
- **Annual meter curve** — the best: the Datadis or utility CSV (8,760 measured hours).
- **Summer + winter** — two samples (day or week) capture seasonality; the system interpolates the rest of the year.
- **One week** — distinguishes weekdays from the weekend.
- **One day** — the minimum: the same shape every day.
- **Curated profile** — with no customer data, pick the closest typical shape and refine later.
:::

## Calculation conventions

:::callout{tone=info}
The profile is normalized to a canonical 365-day year starting on Monday, without holidays. February 29 and the CSV's DST changes are corrected automatically. The result is deterministic: the same sample always produces the same profile.
:::

# Flujo

:::flow
- **Get the sample** — the meter CSV (Datadis) or knowledge of the customer's usage.
- **Create the profile** — upload the file or draw the shape; it is saved in the organization.
- **Attach it to the project** — next to the customer's annual consumption.
- **Harvest** — the analysis crosses production and consumption hour by hour: real self-consumption, battery contribution and bill savings.
:::

# Tutorial

## Import the meter curve

:::steps
1. Ask the customer for their hourly curve on **Datadis** (datadis.es, with their ID and CUPS) or their utility's private area, and download the CSV.
2. Upload the file in the **Consumption profile** section: hourly or quarter-hourly CSV is accepted, for a full year or a complete calendar month.
3. Review the profile name (it defaults to the file name) and save it: it becomes available for this and future projects. If the profile belongs to the customer, its annual consumption automatically fills the **Necesidad anual** field.
:::

:::callout{tone=warning}
If the CSV is incomplete (days missing from the month), the system rejects it and lists the missing days. Download the full range again.
:::

## Without customer data

:::steps
1. Pick a **curated profile** that resembles the real usage: residential evening, remote work, office, retail, industrial or irrigation.
2. Or draw the shape by hand: relative consumption per hour, with variants for Saturday, Sunday and per season.
3. When the customer shares their real CSV, create the measured profile and swap it on the project: the calculations refine without touching anything else.
:::

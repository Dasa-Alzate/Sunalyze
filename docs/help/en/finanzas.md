---
source_hash: 1f9b5d0da731
title: Financial study
routes:
  - finanzas
order: 70
keywords: [finance, npv, irr, payback, capex, subsidies, scenarios, savings]
---

# Concepto

The finance workspace calculates the economic viability of a photovoltaic installation: simple and discounted payback, IRR, NPV, LCOE, ROI and CO₂ savings — all based on the CAPEX, electricity tariff and lifecycle assumptions you define.

:::callout{tone=brand}
This section requires the **finance** flag in your organisation. If it does not appear in the menu, contact your administrator.
:::

:::cards
- **Study** — set your assumptions and see results instantly.
- **Scenarios** — save, compare and reload different versions of the same analysis.
- **Savings study** — client-facing view showing expected savings.
:::

# Criterio

## Indicators calculated by Sunalyze

| Indicator | Description |
|---|---|
| Simple payback | Years without monetary discounting. |
| Discounted payback | Years applying the discount rate. |
| IRR | Internal rate of return of the project. |
| NPV | Net present value at the configured discount rate. |
| LCOE | Levelised cost of energy generated (€/kWh). |
| ROI | Return on investment over the useful lifetime. |
| CO₂ avoided | Kg in year 1 and over the full lifetime. |

## Subsidies

Enabling **Include grants (indicative best case)** lets you select the autonomous community and municipality to include regional and local incentives (IBI + ICIO property tax reductions). The total is indicative: it does not model incompatibilities or real administrative requirements.

:::callout{tone=warning}
The subsidy amount is an indicative best case: it does not replace consulting the current official call for applications and does not guarantee approval.
:::

# Tutorial

## Configuring CAPEX and assumptions

:::steps
1. Go to **Finances** — URL `/app/finanzas`.
2. Select the project in the dropdown in the top bar.
3. In the **CAPEX mode** field choose «Total» (a single amount) or «Breakdown (equipment / labour / legalisation)» and enter the figures excluding VAT.
4. Adjust the **Electricity tariff (€/kWh)**, **Annual consumption (kWh)** and **Surplus price (€/kWh)**.
5. Review the **Study assumptions** section: useful lifetime, discount rate, tariff escalation, annual degradation and O&M cost.
6. If the installation is financed, enable **Financed** and enter the amount, interest rate and term.
7. Results appear in the right-hand panel in real time.
:::

## Saving and comparing scenarios

:::steps
1. Enter a name in **Scenario name** (e.g. «Cash payment with subsidies»).
2. Click **Save scenario**: it is stored with all assumptions and results.
3. Go to the **Scenarios** tab to see the list and compare indicators side by side.
4. Click **Load** on a scenario to restore its assumptions to the study form.
:::

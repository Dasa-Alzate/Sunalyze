---
source_hash: 6c304dd8c050
title: Technical report
routes:
  - memoria
order: 55
keywords: [report, pdf, technical report, protections, budget, generate, sign]
---

# Concepto

The Technical report view brings together all the data needed to produce the PDF document delivered with the installation: client data, electricity contract, system configuration, protections and budget. On the right, a **Document preview** updates in real time to reflect every change you make in the fields.

## Form sections

:::cards
- **Client and location** — client name, town, address, postcode and land registry reference.
- **Electricity contract** — supplier, CUPS, contracted power, voltage, voltage type and system goal (with or without feed-in).
- **Configuration** — peak power (kWp), number of panels, MPPT inputs, panel location and layout, and inverter location.
- **Protections** — DC circuit breaker (max voltage and amperage), AC circuit breaker, AC differential, surge protector and earth cable length.
- **Budget** — line-item budget editor, available when the report is opened from a saved project.
:::

Each section has a status indicator: green when all required fields are filled, amber when some are missing, and grey when untouched.

# Tutorial

## Fill in and preview

:::steps
1. Open the report from a project (the **Report** button in the design step) or go to `/app/memoria` for a free draft.
2. Expand the **Client and location** section by clicking its header and fill in the required fields.
3. Continue with **Electricity contract**, **Configuration** and **Protections**. The preview on the right updates automatically.
4. If you open the report from a project, many fields are pre-filled with the design data.
:::

:::tip{tone=info title="Save without generating the PDF"}
Click **Save** to persist the data in the project without changing its status. Useful for closing the session and resuming later.
:::

## Generate the PDF

:::steps
1. Make sure all section indicators are green (no pending fields).
2. Click **Generate PDF** — the system validates the fields and, if everything is correct, generates the document and opens it in a new tab.
3. If required fields are missing, a warning appears listing the first ones and the relevant section expands so you can see them.
4. When generating from a project, the project status automatically changes to «Report».
:::

:::callout{tone=warning}
Only users with the **Sign report** permission can generate the PDF. If the **Generate PDF** button is disabled, contact your workspace administrator to assign you the appropriate role.
:::

## Add the budget

:::steps
1. The **Budget** section only appears when the report is linked to a saved project.
2. Expand it and use the line-item editor to adjust materials, labour and taxes.
3. Click **Save** in the budget editor; the preview updates with the new total.
:::

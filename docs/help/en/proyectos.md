---
source_hash: 9ad547c2e95a
title: Projects
routes:
  - proyectos
order: 20
keywords: [projects, list, status, filters, duplicate, export, trash]
---

# Concepto

The Projects view is the full list of all designs in your workspace. From here you can search, filter by status, duplicate or delete projects, and export the data to CSV or Excel.

## Table columns

Each row represents a project and includes: **Client / Address**, **Panel** (model and number of units), **kWp**, **Status** and **Modified** (relative time since last edit).

## Project statuses

:::cards
- **Draft** — design in progress, equipment not yet confirmed.
- **Analysis** — equipment selected, production calculated.
- **Layout** — modules placed on the roof.
- **Report** — technical report generated and ready to sign.
:::

# Tutorial

## Search and filter

:::steps
1. Type in the **Search client or address…** field to filter by client name or address instantly.
2. Use the **All statuses** dropdown to narrow down to a specific status.
3. If no projects match, the **Clear filters** button appears to restore the full view.
:::

## Create, duplicate and delete

:::steps
1. Click **New project** in the top bar to open the design wizard from scratch.
2. On any row, click the copy icon to **Duplicate** that project — an immediate copy is created with all its data.
3. Click the trash icon to **Delete** — the system asks for confirmation and the project moves to the bin (recoverable from the «Trash» section).
:::

:::tip{tone=info title="Undo a deletion"}
After deleting, a notice appears with an **Undo** button for a few seconds. Click it to restore the project without going to the trash.
:::

## Export

:::steps
1. Click **Export** in the toolbar.
2. Choose the format (CSV or Excel). The currently filtered list is downloaded with the columns: Client, Address, Panel, kWp, Status and Modified.
:::

## Paginate

When there are more than ten projects, a pagination bar appears at the bottom of the table. Use **Previous** and **Next** or the page indicator to move between pages of ten records.

:::tip{tone=brand title="Keyboard shortcut"}
With the mouse over a row, press **Cmd + D** (Mac) or **Ctrl + D** (Windows) to duplicate that project without using the mouse.
:::

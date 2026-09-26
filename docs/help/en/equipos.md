---
source_hash: 8a3dfa04612a
title: Equipment library
routes:
  - equipos
  - equipos/panels
  - equipos/inverters
  - equipos/batteries
  - equipos/wires
  - equipos/marketplace
order: 50
keywords: [equipment, panels, inverters, batteries, cables, catalog, marketplace, import]
---

# Concepto

The Equipment library centralises all equipment available in your workspace: solar panels, inverters, batteries and cables. Equipment is grouped into **catalogs**; you can have your own catalogs and subscribe to shared catalogs from the **Marketplace**.

## The five tabs

:::cards
- **Panels** — photovoltaic modules with Voc, Vmp, Imp, dimensions and list price.
- **Inverters** — inverters with AC/DC power, Vmax, maximum input and output currents.
- **Batteries** — accumulators with nominal capacity, usable capacity, power, voltage and technology.
- **Cables** — sections with type, material (Cu/Al), cross-section in mm², maximum current and number of conductors.
- **Marketplace** — official and third-party catalogs you can add or remove from your library with one click.
:::

## Own catalogs and the Marketplace

Each piece of equipment belongs to a catalog. Own catalogs (user icon) are editable; marketplace catalogs (store icon) are read-only and are identified by the lock icon in the actions column. Equipment imported automatically from external sources carries the **Scraped** badge.

# Tutorial

## Add equipment manually

:::steps
1. Open the relevant tab (e.g. **Panels**).
2. Click **Add panel** in the top right corner.
3. Fill in the required fields: **Name**, **Power (W)**, **Voc (V)**, **Vmp (V)**, **Imp (A)**.
4. Fill in any optional fields you have (dimensions, price, datasheet URL…).
5. If you have several own catalogs, choose the target **Catalog** in the top dropdown of the drawer.
6. Click **Save**. The equipment appears immediately in the table.
:::

## Bulk-import equipment

:::steps
1. On the desired tab, click **Import**.
2. Download the **TSV template** with the corresponding button and fill in one row per item.
3. Drag the file to the upload area or click to browse (TSV, CSV or Excel, max 2 MB).
4. When done you will see a summary: items created, updated, and, if any, rows with errors.
:::

:::tip{tone=info title="Automatic catalog"}
If you have no own catalog yet, the first item you add or import is saved in «My equipment», which is created automatically.
:::

## Subscribe to a Marketplace catalog

:::steps
1. Go to the **Marketplace** tab.
2. Find the catalog you are interested in — official catalogs carry the **Official** badge.
3. Click **Add to my library**. The equipment becomes available immediately in the panels, inverters, etc. tabs.
4. To remove it, go back to the Marketplace and click **In your library · Remove**.
:::

## Export the library

On any tab (except Marketplace) use the **Export** button to download the current view in CSV or Excel. You can filter by catalog first using the **All catalogs** dropdown to export only a subset.

:::callout{tone=warning}
Marketplace equipment cannot be edited or deleted from the library. To modify it you must duplicate the item to an own catalog or contact the catalog owner.
:::

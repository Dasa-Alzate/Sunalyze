---
source_hash: daaa7c97cf9b
title: Installation tracking (After-sales)
routes:
  - posventa
order: 80
keywords: [after-sales, installations, maintenance, incidents, performance, visits, warranty]
---

# Concepto

After-sales is the post-installation tracking module. Each installation is created from an approved project and brings together maintenance history, open incidents and real production readings in one place.

:::cards
- **Operativa** — installation with no active alerts.
- **Incidencia** — at least one open or in-progress incident exists.
- **Mantenimiento** — a maintenance visit is upcoming or in progress.
- **Baja** — installation out of service or decommissioned.
:::

:::tip{tone=info title="Feature flag"}
After-sales may be disabled in your organisation. If you don't see the section in the side menu, ask your platform administrator to enable it under **Configuración → Flags**.
:::

# Tutorial

## Create an installation

:::steps
1. Open **Posventa** in the side menu.
2. Click **Convertir en instalación**.
3. In the dialog, choose the **Proyecto aprobado** you want to activate and click **Crear instalación**.
4. The installation appears in the list with the default status **Operativa**.
:::

## Manage maintenance

:::steps
1. Open an installation from the list.
2. Go to the **Mantenimiento** tab to see scheduled visits.
3. Use the new visit form to record the type (**Preventivo** / **Correctivo**), date and notes.
4. Change each visit's status to **Realizada** or **Cancelada** when appropriate.
:::

## Log incidents

:::steps
1. In the installation detail, go to the **Incidencias** tab.
2. Create a new incident with its severity: **Baja**, **Media**, **Alta** or **Crítica**.
3. Update the status to **En proceso** or **Resuelta** as the resolution progresses.
4. The installation's global status automatically switches to **Incidencia** while any incident remains open.
:::

## Check performance

:::steps
1. Go to the **Rendimiento** tab of the installation.
2. Click **Añadir lectura** to record the actual accumulated production.
3. The gauge shows the actual/expected ratio: green ≥ 90%, amber ≥ 70%, red below that.
4. The expected value comes from the analysis of the converted project.
:::

:::callout{tone=warning}
Readings are entered manually. For reliable long-term tracking, connect a datalogger or the inverter's API.
:::

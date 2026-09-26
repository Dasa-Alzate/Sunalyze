---
source_hash: 739710548238
title: Legalisation by autonomous community
routes:
  - legalizacion
order: 75
keywords: [legalisation, ccaa, dossier, mtd, processing, self-consumption, autonomous community]
---

# Concepto

The legalisation panel centralises the administrative processing of a photovoltaic installation: dossier status, a step-by-step guide specific to each autonomous community, a presentation assistant, and generation of the official MTD form where the region supports it.

## Status workflow

The dossier progresses through five statuses:

:::flow
- **Draft** — documentation being prepared, not yet submitted.
- **Under review** — internal review before submitting to Industry.
- **Submitted** — dossier registered in the regional electronic office.
- **Approved** — registration in the administrative register confirmed.
- **Rejected** — submission denied; correct and return to draft.
:::

# Criterio

:::norm{code="RD 244/2019"}
Royal Decree 244/2019 governs the administrative, technical and economic conditions for electricity self-consumption. It establishes simplified procedures for installations up to 100 kW on low-voltage grids and registration in the regional self-consumption registry. Each autonomous community runs the procedure through its own electronic office.
:::

:::tip{tone=info title="17 autonomous communities available"}
The selector supports all seventeen Spanish autonomous communities. If the project has saved coordinates, Sunalyze automatically detects the region via reverse geocoding (OpenStreetMap Nominatim) and shows a confirmation notice.
:::

# Tutorial

## Assigning the autonomous community and viewing the guide

:::steps
1. Open a project and navigate to **Legalisation** from the menu or project list.
2. In the **Autonomous community** card, open the **Where the installation is processed** dropdown and choose the community — or wait for Sunalyze to detect it automatically if the project has coordinates.
3. If a guide exists for that region, the processing platform, submission steps, and official procedures and forms with direct links will appear.
4. Forms marked with **Generatable from Sunalyze** can be downloaded using the **MTD official form** button in the top bar.
:::

## Recording the dossier and advancing the status

:::steps
1. In the **Dossier status** card, click the relevant transition button: **Send for review**, **Mark as submitted**, **Mark as approved** or **Mark as rejected**.
2. Once submitted to Industry, enter the dossier number in the **Industry dossier number** field and set the **Submission date**.
3. Click **Save dossier** to record it in the project.
:::

## Using the presentation assistant

When the autonomous community has an assistant available, the **Presentation assistant** card appears with the project data in the exact order required by the electronic office form.

:::steps
1. Open the regional electronic office in another browser tab.
2. For each form field, find the corresponding data in the assistant and click the copy icon to copy it to the clipboard.
3. Paste it into the electronic office form. Signing and submitting are done by you with your digital certificate.
:::

:::callout{tone=info}
If your role does not include the **project:legalize** permission, the transition buttons and dossier field are disabled. Ask your administrator to adjust your role if you need to change the status.
:::

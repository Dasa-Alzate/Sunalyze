---
source_hash: 19fda709e0c9
title: Document templates
routes:
  - plantillas
order: 65
keywords: [templates, documents, report, proposal, variables, builder, library]
---

# Concepto

Templates let you create and reuse structured documents — calculation reports, commercial proposals, legal documents and case analyses — with variables that are filled in automatically with the real data of each project.

:::callout{tone=brand}
This section is only available if the **templates** flag is enabled in your organisation. Contact your administrator if you do not see the option in the menu.
:::

:::cards
- **Bank** — templates shared across the whole organisation, created by your colleagues or imported.
- **My templates** — templates you have created yourself.
- **Library** — the selection of templates installed in your workspace, with labels and favourites to keep them organised.
:::

## Document types

Each template has a type: **Calculation report**, **Legal document**, **Commercial proposal** or **Case analysis**. The type determines which project variables are available in the editor.

## Template statuses

A template moves through three statuses: **Draft** (editable, not visible to clients), **Published** (ready to generate documents) and **Archived** (retired from active use).

# Tutorial

## Creating a new template

:::steps
1. Go to **Templates** — URL `/app/plantillas`.
2. Click **New template** in the top bar.
3. Fill in the name, document type and description in the dialog and confirm.
4. The template editor opens. Use **Add section** to add text blocks.
5. In each section, write the body and click **Insert variable** to add `{{ variable }}` expressions with project data.
6. Click **Save** to keep the draft, or **Publish** to make it ready for use.
:::

## Filtering and organising the library

:::steps
1. Switch to the **Library** tab to see the templates installed in your workspace.
2. Use the **Stage** and **Country** filters to narrow the search; enable **Favourites** to show only starred templates.
3. Click **Organise** on a card to assign categories and labels to it.
4. Click **Remove from selection** if you no longer need that template in the library.
:::

:::tip{tone=info title="Official templates"}
Templates marked with the **Official** badge are system templates: you can use and assign them to projects, but not edit them. Duplicate them if you need to customise them.
:::

## Installing a template from the bank

:::steps
1. In the **Bank** or **My templates** tab, find the card you want.
2. Click **Install**: the template moves to your **Library**.
3. From the Library you can mark it as a favourite or assign labels to it.
:::

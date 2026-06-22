# Plan frontend del módulo financiero (Fase 3)

Cierra la rama `feature-finance`. Reusa el design system y patrones existentes; sin
dependencias nuevas; todo detrás del flag `finance`.

## Contratos backend (ya implementados)

- `POST /api/projects/<id>/financial/compute` con body
  `{assumptions, production_kwh_year?, self_consumption_ratio?, apply_subsidies, ccaa?, municipio?}`.
  `assumptions` = `FinancialAssumptions` (capex_total **o** desglose equipo/mano_obra/legalización,
  iva_pct, tariff_eur_kwh, annual_consumption_kwh, self_consumption_ratio?, surplus_price_eur_kwh,
  lifetime_years, discount_rate, tariff_escalation_pct, panel_degradation_pct, om_cost_eur_year,
  emission_factor_kg_kwh, financing? {amount, interest_rate, term_years}, incentives[]).
  Respuesta `{inputs, capex, annual_saving_year1_eur, incentives:{items,total_eur},
  metrics:{payback_simple_years, payback_discounted_years, roi, irr, npv_eur, lcoe_eur_kwh,
  co2_avoided_year1_kg, co2_avoided_lifetime_kg}, cashflow:[{year, cashflow_eur,
  discounted_cashflow_eur, co2_avoided_kg, ...}]}`.
- CRUD escenarios: `GET/POST .../financial/scenarios`, `GET/PATCH/DELETE .../scenarios/<sid>`.
  Cada escenario guarda `assumptions` + `results` cacheados + flags `is_default`, `apply_subsidies`,
  `ccaa`, `municipio`.
- Variables `finance.*` ya están en el catálogo de `propuesta_comercial` (template_engine/catalog.py).

## Arquitectura frontend (coherente con templates)

Carpeta nueva `frontend/src/features/finance/`:

- `constants.js`: defaults ES (espejo del backend), opciones CCAA/municipio del catálogo de
  subvenciones, helpers de (de)serialización assumptions <-> formulario.
- `cashflow.js`: builder puro de geometría SVG desde el array `cashflow` (acumulado + línea payback).
- `AssumptionsForm.jsx`: formulario de supuestos (CAPEX total/desglose, tarifa, consumo, ratio
  autoconsumo opcional con "automático del análisis", excedentes, vida útil, descuento, IPC,
  degradación, O&M, financiación toggle, subvenciones toggle + CCAA/municipio + aviso "mejor caso").
- `CashflowChart.jsx`: SVG inline accesible (role=img, title, desc, tabla alternativa).
- `IncentivesBreakdown.jsx`: desglose de incentivos.
- `ResultsDashboard.jsx`: KPIs (Metric) + CashflowChart + IncentivesBreakdown.
- `ScenarioComparison.jsx`: tabla lado a lado de escenarios guardados.
- `SavingsStudy.jsx`: estudio de ahorro client-facing reusando `api.templates.preview` del kind
  `propuesta_comercial` (que ya resuelve `finance.*`); fallback a una vista limpia propia.
- `FinanceWorkspace.jsx`: página raíz; selector de proyecto (como LivePreview), pestañas
  Estudio / Escenarios / Estudio de ahorro; orquesta compute con `debounce`.

### Gating, nav, rutas (igual que templates)

- Ruta `/app/finanzas` envuelta en `<RequireFlag flag="finance">`.
- Item de nav con `flag: 'finance'` en `AppLayout.NAV` (se filtra con `flag(n.flag)`).

### Cómo se dibuja el cashflow (SVG inline, sin libs)

Se acumula `cashflow_eur` año a año empezando en `-initial_investment` (capex.initial_investment_eur).
`cashflow.js` mapea (año, acumulado) a coordenadas viewBox con padding, dibuja un `<path>` de área +
`<polyline>`, eje cero, y una línea vertical en el primer año con acumulado >= 0 (payback). Accesible:
`role="img"`, `aria-labelledby` a `<title>`/`<desc>`, y `<table>` alternativa con los valores.

### Estudio de ahorro

Reusa plantillas `propuesta_comercial`: selector de plantilla publicada de ese kind +
`api.templates.preview(templateId, projectId)` -> HTML con marca. Si no hay plantilla, muestra una
vista propia limpia (KPIs + ahorro + CO₂) orientada a venta.

## Tests (vitest + vitest-axe)

`frontend/src/test/finance.test.jsx`: axe de AssumptionsForm, ResultsDashboard, ScenarioComparison;
ResultsDashboard pinta KPIs desde un `results` mock; VariablePicker muestra grupo `Finanzas` para
`propuesta_comercial`. Mantener verdes los tests previos.

## Verificación

`npm run build && npx eslint src && npm test` en `frontend/`.

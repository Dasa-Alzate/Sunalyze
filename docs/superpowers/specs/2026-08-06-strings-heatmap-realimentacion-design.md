# Strings, heatmap solar y realimentación de producción — diseño

Fecha: 2026-08-06 · Rama: `feature/strings-y-heatmap` (base: `feature/degradacion-gradual`)

## Objetivo

Cerrar tres huecos del flujo tipo Reonic reutilizando lo que ya existe:

1. **Strings conectados** — dimensionado eléctrico de cadenas (ROI-2) y `assignStrings` por fin en uso.
2. **Heatmap de irradiancia** — kWh/m²·año por celda sobre la cubierta, calculado con el motor propio.
3. **Realimentación** — la disposición real (módulos colocados, sombras, orientación) corrige la producción anual.

## Fase 1 — Dimensionado de strings

- Migración: `Inverter` += `mppt_v_min`, `mppt_v_max`, `mppt_count`, `isc_max_per_mppt`; `Panel` += `max_series_fuse_a`. Todos nullable (degradación gradual).
- `app/services/string_sizing_service.py` según `docs/dimensionado-electrico-string-sizing.md` §11.3: `evaluate(panel, inverter, site)` → `series_range`, configuración recomendada, `checks` con veredicto/valor/límite/referencia, `missing`.
  - Vmpp caliente usa `tcv` como proxy de β_Vmp con margen explícito del 3 % y assumption declarada (no conservador sin el dato real).
  - Temperatura de célula caliente: NOCT con T_amb máxima del histórico PVGIS.
- `AnalysisService.calculate` devuelve `string_sizing` cuando hay inversor.
- `fronius.py` captura rango MPP completo, nº de MPPT e Isc máx admisible; re-scrape (~90 modelos). CEC no importa inversores hoy: fuera de alcance.
- UI: tarjeta «Cadenas» en el paso Análisis; módulos coloreados por string en Disposición (`layout.strings`); `CircuitDiagram` pre-rellenado con `panels_per_string`/`num_strings` (editables).

## Fase 2 — Heatmap

- `layoutEngine.js`: `annualShadeFactors` generaliza el muestreo de sombra de la declinación de invierno a las 12 declinaciones mensuales × ángulos horarios, ponderado por elevación solar. Fracción de sombra anual 0–1 por celda.
- `PanelLayout`: toggle «Mapa solar» que pinta las celdas candidatas con `POA anual del análisis × (1 − sombra anual)` y leyenda mín/máx en kWh/m². Escala de color según skill dataviz.

## Fase 3 — Realimentación

- El cliente construye `layout_summary = { placed_panels, shade_loss_pct, orientation_loss_pct }` y lo envía en `analyze()`.
- Backend: potencia de campo con módulos colocados; `annual_production_layout = producción × (1 − sombra) × (1 − orientación)`; ambas cifras en la respuesta; la memoria usa la realimentada.
- Recalculo automático con debounce al editar la disposición (PVGIS cacheado 30 días).
- Horizonte PVGIS: ya aplicado vía `usehorizon=True` — sin cambios.

## Trade-off arquitectónico aceptado

La geometría de sombras vive solo en el cliente; el backend recibe `shade_loss_pct` como dato declarado y lo registra como assumption. Se descarta portar el motor a Python (duplicación de mantenimiento, YAGNI).

## Validación

Suite existente (pytest + vitest), sin tests nuevos (norma del proyecto). Validación visual con la app real y proyecto de prueba. Compatibilidad: todos los campos nuevos opcionales; proyectos sin disposición no cambian de comportamiento.

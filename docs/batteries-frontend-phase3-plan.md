# Baterías — Fase 3 (Frontend) · Análisis y plan

## Contexto
Backend (Fases 1-2) ya en `feature-batteries`. Esta fase replica el patrón de inversor en el frontend.

## Shapes confirmados (backend)
- `Battery.to_dict()`: `id, catalog_id, catalog_nombre, nombre, capacity_kwh, usable_kwh, dod, power_kw, voltage, technology, round_trip_efficiency, max_cycles, height, width, depth, datasheet` + provenance + `editable`.
- `/api/batteries` GET/POST/PUT/DELETE igual que `/api/inverters` (mismo `crud.py`). Requeridos: `nombre, capacity_kwh, power_kw, voltage`.
- `Project.to_dict()`: `battery_id`, `battery_quantity` (default 1), `battery_nombre`. Editables vía PUT `/api/projects/:id`.
- Análisis `result.battery` (solo si hay batería): `battery_id, nombre, quantity, bank_usable_kwh, bank_capacity_kwh, round_trip_efficiency, dod, daily_consumption_kwh, daily_production_kwh, daily_surplus_kwh, recommended_usable_kwh, recommended_capacity_kwh, annual_battery_contribution_kwh, self_consumption_uplift_pct, estimated_self_consumption_pct, method, method_note`.
- Variables template `battery.*` ya las entrega `/api/templates/variables/:kind` (VariablePicker es data-driven → aparece solo).
- Diagrama: `/api/circuit/<type>` acepta params `has_battery`, `battery_model`. `CircuitSvg` (diagram-renderer) es passthrough genérico.

## Plan de implementación
1. **api/client.js**: añadir `batteries` (list/create/update/remove) igual que `inverters`.
2. **EquipmentLibrary.jsx**: añadir `batteries` a `SCHEMAS` y a `TAB_ORDER`; estado `data` incluye `batteries`; `invalidateEquipment` lo limpia; `countsLabel` incluye baterías. Reutiliza EditDrawer/columnas (schema-driven).
3. **Wizard.jsx**: cargar `api.batteries.list()`; estado `batteryId`/`batteryQty`; `SearchSelect` clearable de batería (opcional, "Sin batería") + Field cantidad en paso Equipos; enviar `battery_id`/`battery_quantity` en `save()` y `analyze()`; cargar de `proj`. Bloque de resultados de batería (`results.battery`) con KPIs + `method_note` como nota.
4. **template-renderer (MemoriaDocument)**: bloque None-safe de specs de batería cuando `values.battery_nombre`.
5. **MemoriaPreview.jsx**: `seed()` mapea specs de batería del proyecto a `values`; pasarlas a MemoriaDocument y al form POST PDF.
6. **diagram-renderer**: ya soporta params; asegurar que donde se pinta el diagrama del sistema se pasan `has_battery`/`battery_model` (Wizard/preview si aplica). UnifilarStrip admite nodo batería opcional.
7. **VariablePicker**: verificación (sin cambios) — battery.* llega del endpoint.

## Tests (axe + render)
Añadir a `src/test/` casos axe: form batería de EquipmentLibrary (EditDrawer con schema baterías), selección batería en Wizard (SearchSelect), bloque de análisis de batería. Mantener verdes los previos.

## Verificación
`npm run build && npx eslint src && npm test`

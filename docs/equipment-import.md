# Importación de equipos (paneles/inversores/baterías/cables)

## Investigación

### Estado actual relevante
- `frontend/src/features/equipment/EquipmentLibrary.jsx`: `SCHEMAS` define, por tipo,
  `fields[]` (`key`, `label`, `num`, `required`, `select`). El export (`exportCurrent`)
  usa `columns` + `exportRows`. El alta/edición usa el patrón `Scrim` + `sun-drawer`.
- `app/routes/crud.py`: `RESOURCES` mapea cada recurso a `model`, `required`, `fields`,
  `numeric`, `integer`, `defaults`. Rutas con `@require_permission`, ruta con conversor
  `<any(panels,inverters,batteries,wires):resource>`. `_validate_ranges` solo cubre paneles.
- `app/services/catalog_service.py`: `ensure_default_catalog(org_id)` crea/devuelve el
  catálogo propio «Mis equipos» de la org (editable, NO oficial). `resolve_target_catalog`
  valida un `catalog_id` propio.
- Modelos: `nombre` es `unique=True` GLOBAL (no por catálogo) en panels/inverters/batteries.
  `wires` no tiene `nombre`; su identidad natural es `(tipo, material, seccion, no_conductores)`.
- Errores: `app/errors.py` -> `ValidationError` (422, `code='error.validation'`), handler
  central serializa `{error, code, details}`.
- CSRF: Flask-WTF double-submit; cabecera `X-CSRFToken` desde cookie. `client.js` ya la
  añade en mutaciones JSON; para multipart hace falta un helper que la incluya sin fijar
  `Content-Type` (lo pone el navegador con el boundary).
- `config.py`: `MAX_CONTENT_LENGTH` global = 16 MiB.

### Decisiones de dominio
- Clave natural para upsert: `nombre` (panels/inverters/batteries), tupla física (wires).
- Destino del upsert: catálogo propio de la org (`ensure_default_catalog` o `catalog_id`
  propio opcional). Nunca el oficial.
- Cabeceras de la plantilla TSV = las `key` de `SCHEMAS[tipo].fields` (nombres de campo del
  modelo). Contrato limpio: lo que emite la plantilla es exactamente lo que espera el import.

## Plan

### Backend
1. `app/schemas/catalog.py`: añadir `InverterSchema`, `BatterySchema`, `WireSchema` (rangos
   físicos, campos opcionales para validación parcial), como ya hace `PanelSchema`.
2. `app/services/equipment_import.py` (servicio puro, sin Flask salvo db/models):
   - `parse(filename, content) -> list[dict]`: csv/tsv con stdlib (delimitador por
     extensión + sniff), xlsx/xls con `openpyxl` (import perezoso). Cabecera -> campos.
   - `run(resource, cfg, org_id, filename, content) -> {created, updated, errors}`:
     coerción por `cfg`, validación de requeridos + rangos (schema por recurso), upsert por
     clave natural en el catálogo propio, savepoint por fila (no aborta todo; captura
     `ValidationError`/`IntegrityError` como error de fila).
3. `app/routes/crud.py`: endpoint `POST /api/<...>/import` (multipart,
   `@require_permission(EQUIPMENT_EDIT)`). Valida extensión + MIME en el conjunto permitido y
   límite de tamaño (2 MiB) además del global; rechaza con 422 + `code`. Delega en el servicio.
4. `requirements.txt`: `openpyxl` (puro Python).

### Frontend
1. `client.js`: helper `requestForm(path, formData)` con `X-CSRFToken`; `importFile` por recurso.
2. `EquipmentLibrary.jsx`: botón «Importar» junto al export; `ImportDrawer` (Scrim + drawer)
   con pasos, botón de descarga de plantilla TSV (generada en cliente desde `fields`) y zona
   drag-and-drop que al click abre el selector (`accept=".tsv,.csv,.xlsx,.xls"`) y envía al
   backend; muestra resumen creados/actualizados/errores y maneja 422.
3. CSS: clases NUEVAS `eq-import-*` en `app.css` (no tocar reglas de `kit.css`).

### Verificación
- Backend: `python -m unittest discover -s tests`.
- Frontend: `npm run build` + `npx eslint src` + `npx vitest run`.
</content>
</invoke>

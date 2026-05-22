# Baterías - Fase 1 (backend core)

Replica exacta del patrón Inverter/Panel. Sin frontend ni cálculo de autoconsumo (fases 2/3).

## Modelo `Battery(BaseModel, ProvenanceMixin)`
- `catalog_id` FK + `catalog = relationship('Catalog')`.
- Vitales (NOT NULL): `nombre` (unique), `capacity_kwh`, `power_kw`, `voltage`.
- Nullable: `usable_kwh`, `dod` (%), `technology` (str, p. ej. LiFePO4), `round_trip_efficiency` (%),
  `max_cycles` (int), `height`/`width`/`depth` (mm, int), `datasheet`.
- `to_dict()` con `catalog_nombre` + `**self.provenance_dict()`.

## Project
- `battery_id` FK nullable -> batteries, `battery = relationship('Battery', foreign_keys=[battery_id])`.
- `battery_quantity` Integer default 1, nullable, `server_default='1'` en migración.
- Ambos en `to_dict()` + `battery_nombre`.

## Catálogo (multi-tenant org vs oficial org_id=NULL)
- `catalog_service.py`: `_counts` añade `batteries`; `delete_catalog` borra Battery; imports.
- `crud.py`: `RESOURCES['batteries']` + matcher de ruta `<any(panels,inverters,wires,batteries):resource>`.
  required = vitales; numeric = capacity/usable/dod/power/voltage/efficiency; integer = max_cycles/height/width/depth.
- `catalogs.py`: counts de create incluye `'batteries': 0`.

## data_loader
- Siembra 2 baterías LiFePO4 realistas en catálogos oficiales por marca (BYD, Pylontech).
- `ensure_marketplace`: añade Battery al backfill de huérfanos.

## Scrapers (battery-aware, sin adapter nuevo)
- `base.VITAL['battery'] = ('nombre', 'capacity_kwh', 'power_kw', 'voltage')`.
- `acceptance.GLOBAL['battery']` con block/review:
  - block ranges: capacity_kwh [0.5, 10000], power_kw [0.1, 5000], voltage [12, 2000],
    round_trip_efficiency [50, 100].
  - review ranges: capacity_kwh [1, 50], power_kw [0.5, 30], voltage [40, 1000],
    round_trip_efficiency [85, 100], dod [50, 100].

## metrics
- `_count(Battery)` -> 'batteries'; `_review_count(Battery)` sumado a review_pending.

## __init__
- añadir `battery` al import de `app.models`.

## Migración
- down_revision = '42edc2baf2b1' (head de main). Batch-safe. server_default en battery_quantity='1'.
- Tabla batteries + projects.battery_id/battery_quantity. Sin marcadores autogenerados.

---

# Baterías - Fase 2 (backend: cálculo + circuito + documentos)

Integra el modelo ya existente (Fase 1, migración 9a1c7e4b2f10) en escritura de proyecto,
análisis, diagrama unifilar, catálogo de variables y memoria. NO frontend (Fase 3).

## Heurística de dimensionado y uplift de autoconsumo (v1 pragmático)
Sin simulación horaria (depende de datos horarios de consumo futuros). Modelo de balance diario.

Capacidad útil del banco:
```
usable_per_unit = usable_kwh  ó  capacity_kwh*(dod/100)  ó  capacity_kwh (fallback)
bank_usable_kwh = usable_per_unit * battery_quantity
```
Dimensionado recomendado (capar el excedente exportable de un día):
```
daily_consumption_kwh = (necesidad/1000) / 365
daily_production_kwh   = annual_production / 365
daily_surplus_kwh      = max(0, daily_production_kwh - daily_consumption_kwh*autoconsumo)
recommended_usable_kwh   = daily_surplus_kwh
recommended_capacity_kwh = recommended_usable_kwh / (dod/100)   (si dod; else == usable)
```
Uplift de autoconsumo (la batería desplaza excedente diurno a consumo nocturno), triple cap:
```
deliverable_kwh   = bank_usable_kwh * round_trip_efficiency (frac; default 0.90)
daily_unmet_kwh   = daily_consumption_kwh * (1 - autoconsumo)
daily_battery_kwh = min(deliverable_kwh, daily_surplus_kwh, daily_unmet_kwh)
self_consumption_uplift_pct    = daily_battery_kwh / daily_consumption_kwh * 100
estimated_self_consumption_pct = min(100, autoconsumo*100 + uplift_pct)
annual_battery_contribution_kwh = daily_battery_kwh * 365
```
LÍMITE HONESTO: balance diario promediado, no horario. Asume excedente diurno representativo y
consumo nocturno suficiente para descargar a diario. No modela estacionalidad ni días nublados
consecutivos. Estimación de orden de magnitud para dimensionado comercial; la cifra fina exige
datos horarios (futuro).

## Integración
1. routes/projects.py: battery_id, battery_quantity en _EDITABLE_FIELDS + validación de visibilidad
   por catálogo (CatalogService.visible_catalog_ids), igual que panel/inverter.
2. analysis_service: clave opcional `battery` en el resultado, solo si data trae battery_id.
   Sin batería: clave ausente, resto idéntico (no-regresión).
3. circuit/components/Battery (patrón inverter), exportado; en FullSystemDiagram acoplado al DC
   bus del inversor cuando ac.has_battery. Sin batería: diagrama igual.
4. template_engine catalog+context: entidad `battery` (nombre, capacity_kwh, usable_kwh, dod,
   power_kw, voltage, technology, round_trip_efficiency, max_cycles). build_context None-safe.
5. memoria_service: datos de batería en template_vars (None-safe) cuando el proyecto tenga una.

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

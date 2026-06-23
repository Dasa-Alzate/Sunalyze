# Circuit engine — Frontend (Fase 2)

## Backend contract (ya existente)
- `GET /api/circuit/templates` -> `[{name, label}]`, 7 plantillas:
  `solar-basico`, `solar-con-baterias`, `solar-sin-fusibles`, `solar-con-fusibles`,
  `cc-strings`, `grid-connection`, `full-system`.
- `GET /api/circuit/<template>?<params>` -> SVG (`image/svg+xml`).
- Params requeridos (validados en `CircuitDiagramService.REQUIRED_FIELDS`):
  `panel_model, panel_voc, panel_isc, panels_per_string, num_strings,
   dc_fuse_i, dc_switch_v, dc_cable_section`.
- Toggles: `has_fuses` (default true), `has_battery` (default false).
- AC opcionales: `inverter_model, inverter_power, inverter_output_i, ac_phases,
  ac_mcb_i, ac_rcd_i, ac_rcd_sensitivity, ac_cable_section`.

## Mapeo selectores/toggles -> plantilla
- El desplegable de plantilla (poblado desde `templates()`, mostrando labels) es la
  fuente de verdad.
- Toggles `has_fuses`/`has_battery` aplican solo a la familia solar y eligen:
  - con bateria  -> `solar-con-baterias`
  - sin bateria + fusibles -> `solar-con-fusibles`
  - sin bateria + sin fusibles -> `solar-sin-fusibles`
- Al elegir una plantilla solar en el desplegable, los toggles se sincronizan.
- `has_fuses`/`has_battery` se mandan siempre como params para que el SVG respete
  el estado real.

## Params iniciales desde el proyecto
- `api.projects.get(id)` -> `panel_id, inverter_id, battery_id`.
- `api.panels.list()` / `api.inverters.list()` -> objetos con
  panel: `nombre, voc, isc, imp, power`; inversor: `nombre, power, vmax, I_max_output`.
- Mapeo inicial:
  - `panel_model=panel.nombre, panel_voc=panel.voc, panel_isc=panel.isc`
  - `inverter_model=inverter.nombre, inverter_power=inverter.power,
     inverter_output_i=inverter.I_max_output`
  - `has_battery = !!battery_id`
  - `num_strings=1, panels_per_string` estimado o 1; resto valores por defecto sensatos.

## Integracion
- Patron espejo de `memoria`: ruta proyecto-scoped `/app/diagrama/:id` (+ `/app/diagrama`),
  item de nav `diagrama`, y accion en el Topbar del Wizard "Diagrama unifilar".

## Componentes
- `features/design/CircuitDiagram.jsx`: vista con selector + controles + toggles +
  preview `CircuitSvg` (debounce) + descargar SVG.
- Reusa `CircuitSvg` de `services/diagram-renderer` (no se reescribe el fetch).

## i18n
- Namespace nuevo `circuit` (es/en) registrado en `services/i18n/config.js`.

## Tests (`src/test/circuit.test.jsx`, vitest + vitest-axe)
- axe sin violaciones.
- selector se llena con 7 opciones desde `templates()` mock.
- cambiar plantilla cambia la URL/fetch del preview.
- toggles fusibles/bateria seleccionan la plantilla correcta.

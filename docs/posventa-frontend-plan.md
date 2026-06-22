# Posventa — Fase 2 (frontend) plan

Reutiliza design system `shared/ui`, `shared/format.js`, patrones de `features/finance`
y `features/templates`. Todo tras `useAuth().flag('posventa')`.

## Contratos backend (app/routes/posventa.py)
- `GET /api/installations` -> lista de `installation.to_dict()` (incluye `cliente`, `status`,
  `warranty_until`, `*_count`).
- `POST /api/installations` `{ project_id }` -> crea desde proyecto aprobado (201). Conflict si
  no aprobado o ya tiene instalacion.
- `GET /api/installations/<id>` -> dict + `performance`, `maintenance[]`, `incidents[]`, `readings[]`.
- `PATCH /api/installations/<id>` -> edita `status` (operativa|incidencia|mantenimiento|baja) y
  `commissioned_at|warranty_until|expected_annual_kwh|notes`.
- `GET /api/installations/<id>/performance` -> `{ expected_annual_kwh, actual_total_kwh, ratio,
  reading_count, method, method_note }`.
- CRUD anidado maintenance/incidents/readings (GET/POST + PATCH/DELETE).

## Enumeraciones
- instalacion: operativa|incidencia|mantenimiento|baja
- visita kind: preventivo|correctivo; status: programada|realizada|cancelada
- incidencia severity: baja|media|alta|critica; status: abierta|en_proceso|resuelta

## Componentes
- `constants.js`: mapas estado/severidad -> { label, tone, icon } para Badge.
- `api/client.js`: bloque `api.installations`.
- `InstallationsWorkspace.jsx`: Topbar + lista (tarjetas) + dialogo "Convertir" (selector de
  proyectos aprobados sin instalacion vía `api.projects.list('aprobado')`).
- `InstallationDetail.jsx`: cabecera con estado + SelectField de transicion (PATCH) + tabs.
- `MaintenancePanel.jsx`: lista + dialogo programar + marcar realizada (PATCH status=realizada,
  done_at=hoy).
- `IncidentsPanel.jsx`: lista + dialogo abrir (severidad) + resolver (PATCH status=resuelta).
- `PerformancePanel.jsx`: anadir lectura + gauge SVG inline del `ratio` + aviso cifra indicativa.
- `VisitDialog.jsx`, `IncidentDialog.jsx`, `ReadingDialog.jsx`: Scrim.

## Gating
- Ruta `/app/posventa` tras `RequireFlag flag="posventa"`; item de nav `{ flag: 'posventa' }`.

## Rendimiento (SVG)
Gauge semicircular: arco de fondo + arco verde proporcional a `min(ratio, 1.2)` normalizado.
`role="img"` con `aria-label` describiendo esperado/real/ratio. Aviso textual con `method_note`.

## Tests (posventa.test.jsx)
- axe: lista, detalle, VisitDialog, IncidentDialog.
- PerformancePanel pinta el ratio desde un mock (texto del porcentaje + role img).

# Posventa (Fase 1 - Backend) - Investigacion y Analisis

## Objetivo
Seguimiento del estado de las instalaciones fotovoltaicas tras la entrega al
cliente. Una instalacion nace de un proyecto ya aprobado en el flujo de
legalizacion. Sobre ella se registran visitas de mantenimiento, incidencias
operativas y lecturas de produccion reales, y se compara lo real con el baseline
esperado. Todo detras de la feature flag `posventa` (default OFF).

## Dominio

### Ciclo de vida del proyecto -> instalacion
- Un `Project` recorre `borrador -> en_revision -> presentado -> aprobado` (o
  `rechazado`). Ver `app/services/legalization_service.py`.
- La instalacion solo tiene sentido cuando el expediente esta `aprobado`: es la
  puesta en marcha real. Crear una instalacion desde un proyecto no aprobado es
  un Conflict (409), coherente con el patron de guardas de legalizacion.
- Relacion 1:1: un proyecto produce como mucho una instalacion (`project_id`
  unico). Reintentar la creacion sobre un proyecto que ya tiene instalacion es
  Conflict.

### Baseline de produccion esperada
- El dimensionamiento guarda `annual_production` (kWh/año) en
  `Project.resultados` (JSON). Ver `AnalysisService.calculate` ->
  `result['annual_production']` y `Project.resultados`.
- `expected_annual_kwh` de la instalacion se toma de ese valor si esta
  disponible al crearla; si no, queda nulo y se puede fijar luego.

### Estados de la instalacion
`operativa | incidencia | mantenimiento | baja` (default `operativa`).
Sin maquina de transiciones estricta en v1: cualquier estado conocido es
destino valido (set abierto). Se valida solo que el destino pertenezca al
conjunto. (La legalizacion si usa transiciones estrictas porque es un flujo
administrativo; el estado operativo de una instalacion cambia de forma menos
lineal: puede pasar de operativa a incidencia y volver, entrar en mantenimiento
puntual, o darse de baja.)

### Entidades anidadas
- `MaintenanceVisit`: visitas preventivas/correctivas. `status`
  `programada|realizada|cancelada`, `scheduled_at`, `done_at` (nullable),
  `technician`, `notes`.
- `Incident`: incidencias operativas de la instalacion (NO `SupportTicket`, que
  es soporte de plataforma). `severity` `baja|media|alta|critica`, `status`
  `abierta|en_proceso|resuelta`, `title`, `description`, `opened_at`,
  `resolved_at` (nullable).
- `ProductionReading`: lecturas reales. `period` (texto, p. ej. `2026-05` o
  fecha), `actual_kwh`.

### Resumen esperado-vs-real
- Suma de `actual_kwh` de todas las lecturas vs `expected_annual_kwh`.
- `ratio = actual_total / expected_annual_kwh` cuando hay baseline.
- Nota honesta: el real fiable exige monitorizacion automatica (datalogger /
  API del inversor). v1 = entrada manual de lecturas; el resumen es indicativo,
  no certificado, y no normaliza por periodo cubierto.

## Patrones del repo a imitar
- Modelos heredan `BaseModel` (`id`, `created_at`, `updated_at`), `org_id` FK a
  `organizations.id` con `index=True`. `to_dict()` con `isoformat()` en fechas.
- Servicio sin Flask en `app/services/`, devuelve modelos / lanza DomainError
  (`Conflict`, `NotFound`, `ValidationError`).
- Rutas finas en `app/routes/`, `@require_flag('posventa')` + `@require_permission`,
  IDOR -> 404 via helper `_owned_or_404`. PATCH para updates.
- Multi-tenant por `org_id`; nunca confiar en el `org_id` del cuerpo, usar
  `current_org_id()`.
- Migracion batch-safe, `server_default` en NOT NULL nuevos, sin marcadores
  autogenerados, `down_revision = '67ad717ad9a4'` (head actual).
- Flag en `DEFAULT_FLAGS` (default OFF, visible).
- Permisos: lectura `PROJECT_VIEW`, escritura `PROJECT_EDIT`. Se reutilizan los
  permisos de proyecto (la instalacion es la continuacion del proyecto); no se
  añade un permiso nuevo para no inflar la matriz RBAC.

## Plan de arquitectura
- `app/models/installation.py`: `Installation`, `MaintenanceVisit`, `Incident`,
  `ProductionReading` (constantes de estado por entidad).
- `app/services/installation_service.py`: `InstallationService` con
  `create_from_project`, `set_status`, CRUD anidado y `performance_summary`.
- `app/routes/posventa.py`: blueprint `posventa_bp`, rutas REST.
- Registrar modelos en `app/__init__.py` import y blueprint.
- `posventa` en `DEFAULT_FLAGS`.
- Migracion `<rev>_posventa_instalaciones.py` con las 4 tablas.
- Tests `tests/test_posventa_integration.py`.

## Rutas
```
GET    /api/installations                                  listar (org)
POST   /api/installations            {project_id}          crear desde proyecto aprobado
GET    /api/installations/<id>                             detalle (+ resumen)
PATCH  /api/installations/<id>       {status?, ...}        transicion estado / editar
GET    /api/installations/<id>/performance                resumen esperado-vs-real

GET/POST           /api/installations/<id>/maintenance
PATCH/DELETE       /api/installations/<id>/maintenance/<vid>
GET/POST           /api/installations/<id>/incidents
PATCH/DELETE       /api/installations/<id>/incidents/<iid>
GET/POST           /api/installations/<id>/readings
PATCH/DELETE       /api/installations/<id>/readings/<rid>
```

## Limite honesto
La monitorizacion real (lecturas automaticas desde el inversor/datalogger) es
deuda futura. v1 registra lecturas manuales; el resumen esperado-vs-real es
indicativo.

## Que expone para Fase 2 (frontend)
- `to_dict()` de las 4 entidades + endpoint de `performance` con
  `expected_annual_kwh`, `actual_total_kwh`, `ratio`, `reading_count` y la nota.
- Conjuntos de estados/severidades como constantes del modelo (para selectores).
- Flag `posventa` en el marketplace de modulos.

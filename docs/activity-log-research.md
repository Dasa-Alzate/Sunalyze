# Investigacion + analisis: bitacora de actividad (backlog §1)

Entregable de los pasos 1-2 de feature-iteration para la rama
`feature-activity-log`. La fundacion de auditoria ya existe en `main`; aqui se
construye encima sin reconstruirla.

## 1. Estado de partida (lo que YA existe en main)

- `AuditEvent` (`app/models/audit_event.py`): append-only, org-scoped, indice
  compuesto `(org_id, created_at)`. `action` sigue `dominio.verbo`.
- `AuditService.record(...)` (`app/services/audit_service.py`): `add` + `flush`,
  sin `commit`. El commit lo hace el llamador junto a su mutacion -> atomicidad.
  `list_for_org(org_id, limit)` lee la bitacora mas reciente primero.
- `GET /api/audit` (`app/routes/audit.py`): permiso `audit:view`, scoped al
  `current_org_id()`. Soporta solo `limit`.
- `SoftDeleteMixin` (`app/models/database.py`): `deleted_at`, `is_deleted`,
  `soft_delete()`, `active()` (excluye borrados), `with_deleted()`. Ya aplicado
  a `User` y `Organization`.
- Ya auditan: `project.create`, `project.update`, `project.delete`.

## 2. Decisiones de dominio

### Feed de actividad
- Paginacion por `limit`/`offset` (offset-based: suficiente para una bitacora
  administrativa, sin necesidad de cursor estable a alta escala). `total` y
  `has_more` para que el frontend pinte paginacion.
- Resolver de enlaces `entity_type -> ruta` en backend para que el frontend
  enlace al objeto sin conocer el routing de la app. Mapa estatico:
  - `project -> /app/proyectos/<id>`
  - `catalog -> /app/equipos` (los catalogos no tienen vista de detalle propia;
    se enlaza a la biblioteca de equipos)
  - `equipment` y subtipos -> `/app/equipos`
  - entidades sin ruta conocida o sin `entity_id` -> `link: null`.
- El enlace se calcula en una capa de presentacion (`to_feed_dict`) sin tocar
  el `to_dict` canonico del modelo (que es generico y no debe acoplar rutas de
  frontend).

### Cobertura de audit ampliada (dominio.verbo)
- Equipos (`crud.py`): `equipment.create`, `equipment.delete`. El `payload`
  lleva `resource` (panels/inverters/...), `nombre`, `catalog_id`. El update no
  se audita por ahora (no estaba pedido como clave; alcance conservador), pero
  queda anotado.
- Catalogos (`catalogs.py` / `catalog_service.py`): `catalog.create`,
  `catalog.delete`, `catalog.subscribe`, `catalog.unsubscribe`,
  `catalog.restore`.
- Soft-delete/restore: `project.restore`, `catalog.restore`. El `project.delete`
  y `catalog.delete` siguen registrando, ahora describiendo un borrado logico.

### Soft-delete + restore (solo Project y Catalog)
- `SoftDeleteMixin` aplicado a `Project` y `Catalog`.
- `DELETE` -> `soft_delete()` (no `db.session.delete`). El AuditEvent va en la
  MISMA transaccion (`record(...)` + `commit`).
- Lectura/listado filtran explicitamente con `.active()` o
  `filter(deleted_at.is_(None))` — NO se instala un filtro global por evento de
  SQLAlchemy, para no alterar el comportamiento de otras queries (p. ej. las que
  cuentan equipos por catalogo, joins de proyecto, etc.).
- Restore: `POST /api/projects/<id>/restore` (permiso `project:delete`) y
  `POST /api/catalogs/<id>/restore` (permiso `catalog:manage`). Multi-tenant
  (IDOR -> 404), buscan en `with_deleted` y ponen `deleted_at = None`.

### Unicidad de nombre de Catalog vs filas borradas
- NO hay constraint UNIQUE en `catalogs.nombre` en la BD (verificado en las
  migraciones). La unicidad efectiva la da hoy solo
  `ensure_default_catalog` con un `filter_by(org_id, nombre).first()`.
- Decision: al validar unicidad / resolver el catalogo por defecto se filtra
  por filas ACTIVAS (`deleted_at IS NULL`). Asi un catalogo "Mis equipos"
  borrado logicamente no bloquea la recreacion del default ni colisiona con uno
  nuevo del mismo nombre. `ensure_default_catalog` pasa a usar `.active()`.

## 3. Lo que queda DIFERIDO (anotado, no se hace aqui)
- Soft-delete amplio a equipos (panels/inverters/batteries/wires) y a
  `Membership`: hoy `equipment.delete` y la baja de miembros siguen siendo
  borrado fisico. Bajo blast-radius primero.
- Revert con cascada DAG (Fase 3): deshacer una accion auditada propagando por
  el grafo de dependencias. Diferido por riesgo.
- Filtro global de soft-delete por evento de SQLAlchemy: descartado por ahora
  para no cambiar el comportamiento de queries existentes.
- `equipment.update` / `catalog` rename audit: no incluido (no era accion clave
  del alcance).

## 4. Verificacion
- Migracion batch-safe, `server_default` no aplica (columna nullable
  `deleted_at`), sin `# ###`, `down_revision = '827266176ee7'` (head de main).
- Tests unittest (sqlite aislada): soft-delete de project/catalog, restore,
  unicidad ignora borrados, feed paginado + enlace resuelto, cobertura de
  equipos/catalogo, no-regresion del CRUD existente.

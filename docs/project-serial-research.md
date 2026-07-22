# Project serial — investigación y plan

## Objetivo
Número de serie correlativo **por organización** para cada proyecto, con prefijo
configurable (`OrgBrandingProfile.project_prefix`, String(8)). Formato mostrado:
`PREFIJO-0001` (relleno a 4 dígitos) o `0001` si no hay prefijo. Inmutable: se asigna al
crear y no cambia; solo el prefijo (branding) puede variar y se refleja al vuelo.

## Estado actual relevante
- `Project(BaseModel, SoftDeleteMixin)` en `app/models/project.py`; `org_id` nullable con
  FK CASCADE; soft-delete vía `deleted_at`. `to_dict()` serializa el proyecto.
- `OrgBrandingProfile` (1:1 con org) ya tiene `project_prefix` (migración `e7f8a9b0c1d2`,
  head único actual).
- `OrgService.get_branding(org_id)` devuelve dict del branding (o defaults) incluyendo
  `project_prefix`. Sin fila de branding, `project_prefix` es `None`.
- Rutas que crean proyectos: `create_project` y `duplicate_project` en
  `app/routes/projects.py`. Listado en `list_projects` / `list_deleted_projects` (siempre
  scoped a `current_org_id()`).
- `SoftDeleteMixin.with_deleted()` == `cls.query` (sin filtro de `deleted_at`).

## Decisiones de diseño
1. `serial_seq` Integer nullable en `projects`. Correlativo por org (1..N). Inmutable.
2. Asignación con `Project.next_serial_seq(org_id)` (classmethod): `max(serial_seq)` de la org
   **incluyendo soft-deleted** + 1, para no reutilizar números. Carrera posible en alta
   concurrente (volumen bajo, aceptable) — documentado en el docstring.
3. `to_dict(prefix=_UNSET)`: si no se pasa prefijo, se lee perezosamente del branding de la
   org del proyecto. En listados (misma org) se calcula el prefijo una vez y se pasa a todos
   los `to_dict` → evita N+1. `serial` = `formatted_serial(prefix)`: `{pref}-{seq:04d}` con
   guion si hay prefijo, `{seq:04d}` si no; `None` si `serial_seq` es `None`.
4. Migración batch-safe: añade `serial_seq` (nullable) y backfilla los proyectos existentes
   numerándolos 1..N por org en orden `created_at` (incluye borrados). `down_revision` =
   `e7f8a9b0c1d2`. Head único.

## Frontend
- `ProjectList.jsx`: Badge (shared/ui) con el `serial` junto al cliente.
- `Wizard.jsx`: Badge con el `serial` en la cabecera (Topbar actions) cuando el proyecto ya
  existe.

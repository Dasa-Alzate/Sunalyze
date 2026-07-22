# Configuración + Marca — investigación y plan

## Objetivo
Unificar Flags y Marca bajo una vista `Configuración` (dos columnas, pestañas), dar amor a la
marca (alineación), subir el logo al servidor (carpeta `cfiles`, reemplazo, solo imágenes) y
añadir `project_prefix` a la marca.

## Estado verificado del repo
- Vista Flags: `frontend/src/features/admin/Flags.jsx`; ruta `app/router.jsx:61`
  `admin/flags` con `RequirePlatformAdmin`; nav `AppLayout.jsx:27` `{ key:'flags', platform:true }`.
- Marca: `frontend/src/features/settings/BrandingSettings.jsx`; ruta `organizacion/marca`
  (`router.jsx:58`); nav `AppLayout.jsx:24` `{ key:'marca', perm:'org:manage' }`.
- Endpoints branding: `app/routes/org.py` GET+PATCH `/api/org/branding` con
  `@require_permission(Permission.ORG_MANAGE)`; servicio `app/services/org_service.py`;
  esquema `app/schemas/org.py::OrgBrandingSchema`; modelo
  `app/models/organization.py::OrgBrandingProfile` (logo_path rel. a instance_path,
  primary_color, footer_text).
- Auth front (`AuthProvider`): `isPlatformAdmin` (=`user.is_superadmin`), `can(perm)`,
  `flag(key)`.
- Head de migración único: `d6e7f8a9b0c1` (nada apunta a él como down_revision).
- `MAX_CONTENT_LENGTH` en `config.py:111` (16 MB por defecto).
- Pillow 12.1.1 en `requirements.txt`.
- `pdf_url_fetcher` sirve ficheros bajo `instance_path` (rutas relativas), así que
  `logo_path = cfiles/<org_id>/logo.<ext>` embebe en el PDF sin cambios.
- Errores: pydantic `ValidationError` -> 422 global; `app.errors.ValidationError` (422),
  `NotFound` (404).
- Patrón de tabs existente: `sun-tabs`/`sun-tab`/`sun-tab--active` (horizontal). Para dos
  columnas se añaden clases `sun-cfg*` (nav vertical) en `components.css`.

## Decisiones
1. `Configuracion.jsx` (nuevo) en `features/settings/`, ruta `/app/configuracion`, con Topbar
   propia y layout dos columnas (`sun-cfg`): izquierda lista de pestañas, derecha panel activo.
2. Gating por pestaña: **Marca** si `can('org:manage')`; **Flags** solo si `isPlatformAdmin`.
   Pestaña por defecto = primera disponible.
3. Nav: se elimina el ítem `flags` (platform) y el ítem `marca`; se añade `configuracion`
   (`perm:'org:manage'`, icono `settings`). Se borra la ruta `admin/flags` y `organizacion/marca`.
4. `Flags.jsx` se convierte en panel (sin Topbar, con toolbar local para "Nuevo flag").
   `BrandingSettings.jsx` se convierte en panel Marca (sin Topbar) con formulario alineado.
   Backend de flags sigue gateado a superadmin (defensa en profundidad, no se toca).
5. Logo al servidor: `POST /api/org/branding/logo` (multipart), valida tipo real
   (Pillow para png/jpeg/webp + sniff SVG), reemplaza `logo.*` previo, límite 2 MB, actualiza
   `logo_path`. `GET /api/org/branding/logo` sirve el fichero (send_from_directory bajo
   instance_path, valida prefijo `cfiles/<org_id>/`).
6. `project_prefix`: columna `String(8)` nullable en `OrgBrandingProfile`; migración
   encadenada a `d6e7f8a9b0c1`; validación alfanumérico/guion, max 8, upper; expuesto en
   `to_dict`, `OrgBrandingSchema` y PATCH.

## Mantenimiento de tests
- `templates.test.jsx` (BrandingSettings): el campo de logo pasa de texto a subida; se ajusta
  la aserción del label del logo (mantenimiento por cambio de UI).

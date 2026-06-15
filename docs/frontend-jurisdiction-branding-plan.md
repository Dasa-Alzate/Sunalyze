# Tercer commit en `feature-document-framework`: frontend de jurisdicción/tags + branding por org

## Objetivo
Exponer en el frontend lo que el backend ya soporta (jurisdicción, tags, los 8 DocumentKind,
branding por org) y añadir el mínimo backend para alimentarlo.

## Backend (mínimo)
1. `GET /api/templates/kinds` -> `[{key, label}]` desde `DocumentKind.all_meta()`
   (en `template_service` o directo desde el modelo). Gate: `require_flag('templates')` +
   `TEMPLATE_VIEW` (igual que el resto del blueprint de plantillas).
2. Branding por org: nuevo blueprint `app/routes/org.py` (`org_bp`):
   - `GET /api/org/branding` -> branding actual (o defaults vacíos) de `current_org_id()`.
   - `PATCH /api/org/branding` -> upsert de `logo_path|primary_color|footer_text`.
   - Gate: `require_permission(Permission.ORG_MANAGE)` (owner+admin). Multi-tenant por
     `current_org_id()` (sin IDOR; el branding es 1:1 con la org de sesión).
   - Schema pydantic `OrgBrandingSchema` en `app/schemas/org.py`.
   - Servicio `OrgService` en `app/services/org_service.py` (get_or_create + update).
   - `ORG_MANAGE` se añade a `_ADMIN` en `authz.py` (owner ya lo tiene vía ALL_PERMISSIONS).
   - Registrar `org_bp` en `app/__init__.py`.
3. Ampliar schemas de plantillas: `TemplateCreateSchema`/`TemplateUpdateSchema` aceptan
   `country, region, required_by, stage, locale, currency`. `create_template`/`update_template`
   del servicio ya aceptan country/region; añadir el resto de campos al servicio.

## Frontend
- `api/client.js`: `templates.kinds()`, nuevo grupo `org: { getBranding, setBranding }`.
- `constants.js`: `TEMPLATE_STAGES` (diseno|legalizacion|entrega|posventa con label),
  `kindLabel` deja de depender del array hardcodeado de 4 -> los kinds vienen del endpoint;
  se conserva `kindLabel` como fallback. Helper `stageLabel`.
- `CreateTemplateDialog`: selector de kind alimentado por `api.templates.kinds()`, + campos
  country, region, required_by, stage (select), locale, currency. Se envían en create.
- `TemplateBuilder`: cabecera editable con los mismos campos de jurisdicción/tags; guarda vía
  `api.templates.update(id, {...})`. Badges de kind/stage/country/required_by.
- `TemplatesGallery`: badges en tarjetas (kind, country, stage, required_by). Filtros nuevos
  por `stage` y por `country` (client-side sobre la lista ya cargada), además de los
  existentes. Aplican a las tres pestañas (bank/org/library).
- `BrandingSettings.jsx` (feature `settings`): formulario logo_path/primary_color (color
  input + texto)/footer_text vía endpoints branding. Ruta `/app/organizacion/marca`, gateada
  por permiso `org:manage` y nav business-only. i18n namespace `branding`.
- VariablePicker: ya es data-driven por kind (item 6) -> solo confirmar, no tocar.

## i18n
- Nuevo namespace `branding` (es/en) para la vista de branding. Etiquetas de campos del editor
  y filtros vía `t()` con namespace `templates` nuevo (es/en) para no hardcodear.

## Reglas
- Sin comentarios inline. a11y (htmlFor/labels/aria). eslint 0 warnings. Sin migración.

## Verificación
- backend: py_compile, flask db upgrade (BD sqlite aislada), unittest discover.
- frontend: npm run build, eslint src, npm test (axe editor + branding + kind select desde mock).
- Borrar `df3_dev.db`.

# Framework internacional de documentos — investigación y plan

## Objetivo
Hacer el framework de generación de documentos internacional y extensible. Un solo commit
estructural; los nuevos *tipos* de documento (siembra de plantillas system) van en un commit
posterior aparte.

## Estado actual (hechos)
- `DocumentKind` es una clase de constantes con 4 kinds y `ALL`.
- `ReportTemplate` ya tiene `country`/`region`/`scope`. Hereda `BaseModel`.
- Catálogo de variables (`catalog.py`): code-as-config, grupos por entidad, whitelist derivada.
  Las labels de `finance.*` llevan `€` hardcodeado.
- Resolver (`context.py`): None-safe, lee solo whitelist. `ContextResolver(context, allowed)`.
- Filtros (`filters.py`): `number`/`thousands` fijan coma decimal y punto de miles (es-ES).
  `apply_filter(name, value, args)` pasa solo args literales del pipeline.
- `render_version(content, project, user, org, on_error)` construye contexto + resolver.
- `document_service._wrap_html` fija `lang="es"` y `@page { size: A4 }`.
- Modelos posventa (`installation.py`): `Installation`, `MaintenanceVisit`, `Incident`,
  `ProductionReading`. Org-scoped. Installation 1:1 con Project.
- `Organization` no tiene branding.
- Head de migraciones: `a1b2c3d4e5f6`. No hay babel instalado -> formateo de locale con stdlib.

## Decisiones de dominio (jurisdicción -> presentación)
- **Perfiles por país** (`jurisdiction.py`): `COUNTRY_PROFILES` con `{locale, currency, page_size}`.
  Default ES. `ReportTemplate.country` dirige; `locale`/`currency` NULLABLE como override explícito.
- **Locale en el render**: el resolver transporta `locale` y `currency`. Los filtros
  `number`/`thousands`/`money`/`date` los leen del resolver (no fijos). Formateo stdlib:
  mapa de separadores por familia de locale (es/de/fr -> coma decimal, punto/espacio miles;
  en -> punto decimal, coma miles).
- **Moneda**: filtro `money` formatea importe segun currency+locale (símbolo y posición).
  Labels `finance.*` quedan neutras (sin `€`).
- **Shell HTML**: `lang` y `@page size` (A4 vs Letter) derivan de la jurisdicción de la plantilla.

## DocumentKind registry (extensible)
- Registro dict por key con metadata: `key`, `label`, `var_groups` (lista de nombres de grupo).
- Conserva los 4 actuales + añade `contrato`, `certificado`, `informe_mantenimiento`,
  `solicitud_conexion`. Añadir un kind = una entrada.
- Backward-compat: constantes (`MEMORIA_CALCULO`...) y `ALL` se mantienen como propiedades.
- El catálogo de variables por kind se deriva del registry (var_groups).

## Variables posventa
- Grupos `installation`, `maintenance`, `incident` (la última visita / incidencia abierta más
  reciente) en el catálogo. None-safe en el contexto. Expuestas en legal/certificado/informe.

## Tags
- `required_by` (String), `stage` (String: diseno|legalizacion|entrega|posventa) en
  `ReportTemplate`, en `to_dict()`. `country`/`region` ya existen.

## Branding
- `OrgBrandingProfile(BaseModel)` org-scoped 1:1: `logo_path`, `primary_color`, `footer_text`.
  Aplicado en el shell del PDF (logo/color/pie) cuando existe.

## Migración
- Una sola, batch-safe, `server_default` en NOT NULL nuevas, `down_revision = a1b2c3d4e5f6`.

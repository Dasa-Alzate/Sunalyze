# Diseño: Scraper de Autosolar + catálogos por marca y gestión de superusuario

Fecha: 2026-06-23
Rama: feature (se crea al iniciar la implementación; nada va a `main`).

## 1. Problema y contexto

El sistema tiene un scraper por **marca/fabricante** (hoy solo Fronius), donde cada
scraper declara `brand` y `kind` únicos y vuelca a un catálogo oficial de esa marca.

Autosolar (`autosolar.es`) es un **distribuidor**, no un fabricante: vende paneles e
inversores de muchas marcas. Esto rompe el supuesto "un scraper = una marca = un tipo"
en `app/scrapers/service.py`.

Decisiones de producto tomadas en el brainstorming:

1. **Marca ≡ entidad `Catalog`.** Cada equipo se enruta al catálogo de su fabricante.
2. **Ningún equipo entra sin marca.** Si el scraper no logra deducir un fabricante para
   un producto, ese producto se rechaza (no se persiste).
3. **Marca nueva → catálogo en cuarentena.** Cuando el scraper deduce un fabricante que
   aún no tiene catálogo, crea el catálogo con `is_active=False`.
4. **Catálogos inactivos son invisibles para usuarios** en toda vista/consulta. Solo el
   superusuario, en el panel server-rendered (`app/superadmin/`), los ve y puede
   activarlos, desactivarlos, mergearlos o hacerles CRUD.
5. **Alcance de tipos en esta iteración: paneles e inversores.** (Baterías fuera; ni
   siquiera están cableadas hoy en `service.py`.)

## 2. Restricciones del esquema que condicionan el diseño

- `Panel.nombre` e `Inverter.nombre` son `unique=True` **global** (no por catálogo).
  - El dedup por nombre debe consultarse de forma **global** (backstop anti-`IntegrityError`).
  - En un merge B→A, reasignar `catalog_id` **nunca colisiona por nombre** (dos filas no
    pueden compartir `nombre`). El conflicto a resolver es **semántico**: el mismo equipo
    con nombre distinto.
- `Catalog` hoy: `nombre`, `descripcion`, `org_id` (NULL = marketplace), `is_official`,
  `SoftDeleteMixin` (`deleted_at`). `org_id=None + is_official=True` = catálogo oficial
  sembrado por scrapers.
- Visibilidad de catálogos pasa por un cuello de botella: `CatalogService` (`own_catalog_ids`,
  `subscribed_catalog_ids`, `visible_catalog_ids`, `library`, `marketplace`, `bootstrap_org`).
- Superadmin: panel server-rendered `app/superadmin/` con IP allowlist + MFA + `SuperadminAudit`,
  ya con un flujo análogo `/equipment/review`.
- Roles: `User.is_superadmin`; permisos org-scoped vía `Membership.role` y `app/authz.py`.
- Migraciones: Flask-Migrate/Alembic. Head actual: `73c21c5757c4`.

## 3. Cambios de modelo de datos

### 3.1 `Catalog` — dos columnas nuevas

- `scraper_name` (`String(100)`, nullable, **indexado**): clave normalizada con la que los
  scrapers referencian la marca (p.ej. `'fronius'`, `'ja solar'`). Permite buscar el
  catálogo por clave estable en vez de por `nombre` (frágil).
- `is_active` (`Boolean`, NOT NULL, `server_default=true`): catálogo publicado/visible.
  `False` = en cuarentena, solo visible para superusuario.

`Catalog.to_dict()` añade `scraper_name` e `is_active`.

### 3.2 Migración

`down_revision = '73c21c5757c4'`.

```
upgrade():
  add_column catalogs.scraper_name  String(100) nullable
  add_column catalogs.is_active      Boolean NOT NULL server_default true
  create_index ix_catalogs_scraper_name
  # backfill: catálogos oficiales existentes -> scraper_name = lower(nombre normalizado),
  #           todos los existentes -> is_active = true (lo cubre server_default)
downgrade():
  drop_index; drop_column is_active; drop_column scraper_name
```

El backfill de `scraper_name` para oficiales se hace en el `upgrade()` con SQL/`op.execute`
usando la misma normalización que el código (sección 4.2). Los catálogos de workspace
quedan con `scraper_name = NULL` (no los tocan los scrapers).

## 4. Componentes del scraper

### 4.1 Contrato — `NormalizedProduct` (`app/scrapers/base.py`)

Añadir campo opcional `brand: str = None`. Cada producto de un distribuidor lo rellena con
el fabricante deducido. Los scrapers mono-marca (Fronius) lo dejan en `None`.

### 4.2 Deducción y normalización de marca (`app/scrapers/brands.py`, nuevo)

- `normalize_brand(raw) -> str`: minúsculas, colapsa espacios/guiones, sin acentos. Es la
  función canónica para `scraper_name`. La usan: scraper, migración (backfill) y merge.
- `KNOWN_BRANDS`: mapa de alias → nombre canónico de display (p.ej. `'jasolar'`,
  `'ja-solar'`, `'ja solar'` → `'JA Solar'`). Sirve para **canonicalizar** y evitar
  catálogos duplicados por variantes tipográficas (reduce falsos negativos).
- `deduce_brand(attr, title) -> (display_name | None, scraper_name | None)`:
  1. Si la página trae atributo de fabricante estructurado (PrestaShop manufacturer /
     schema.org `brand`), se usa — permite descubrir marcas **nuevas** (no en la lista).
  2. Si no, se busca un alias de `KNOWN_BRANDS` dentro del título.
  3. Si ninguno produce marca → `(None, None)` → el producto se rechazará en el servicio.
  El display que venga del atributo se pasa por `KNOWN_BRANDS` para canonicalizar si aplica.

### 4.3 `AutoSolarScraper` (`app/scrapers/autosolar.py`, nuevo)

- Atributos: `brand = 'AutoSolar'` (etiqueta de proveedor: clave de registro, `ScrapeRun`,
  default de acceptance), `requires_product_brand = True`, sin `kind` fijo (multi-tipo).
- `discover()`: semilla de URLs de categoría (paneles, inversores) + paginación cortés →
  refs `{external_id, url, kind}`. `external_id` = slug/SKU de Autosolar.
- `fetch(ref)`: `requests.get` con UA propio (`SunalyzeBot/...`), timeout y pausa entre
  peticiones. Respeta robots.txt/ToS.
- `parse(ref, raw)`: extrae `nombre`, deduce marca (4.2), extrae vitales reutilizando
  `grab()`/`to_float_eu()` de `base.py` + helpers nuevos para tablas de specs. Devuelve
  `NormalizedProduct(kind=ref['kind'], brand=display_o_None, ...)`. Productos sin vitales
  quedan parciales y se descartan por las reglas vitales existentes.

> Riesgo conocido: los vitales de **paneles** (Voc/Vmp/Imp) suelen vivir en tablas de specs
> o PDF; el rendimiento de extracción será menor que en inversores. Aceptable: lo parcial se
> descarta con motivo, igual que hoy.

### 4.4 Registro (`app/scrapers/registry.py`)

`SCRAPERS['autosolar'] = AutoSolarScraper()`. Invocación sin cambios:
`flask scrape run autosolar --dry-run`.

## 5. Orquestación: enrutado por producto (`app/scrapers/service.py`)

Generalizar el servicio (enfoque A elegido):

- **Catálogo por producto, no por scraper.**
  `catalog_brand = product.brand or (scraper.brand if not getattr(scraper, 'requires_product_brand', False) else None)`.
  - `None` → producto a `report['blocked']` con motivo `'sin marca deducida'` (no persiste).
- **Resolución de catálogo por `scraper_name`** (centralizada en `CatalogService.official_catalog`,
  sección 7): busca por `scraper_name = normalize_brand(brand)`; si no existe, lo crea con
  `org_id=None, is_official=True, is_active=False` (cuarentena) y `nombre = display`.
- **Modelo por `product.kind`**: `Model = _MODEL[product.kind]` (no `scraper.kind`). `_MODEL`
  mantiene panel + inverter.
- Cacheo de catálogos resueltos por corrida (dict `scraper_name -> Catalog`).
- `acceptance.evaluate(product, catalog_brand)` (usa la marca del fabricante).
- Fronius queda **funcionalmente intacto**: sin `requires_product_brand`, su `brand='Fronius'`
  resuelve su catálogo por `scraper_name='fronius'`.

### 5.1 Dedup en `_upsert` (acotado a marca, con backstop global)

Resuelto el catálogo de la marca:

1. **external_id** dentro del catálogo de la marca: `(catalog_id, external_id)`.
2. **Nombre normalizado, consulta GLOBAL** (obligado por el `unique` global):
   - Match en el **mismo** catálogo de marca → `update`.
   - Match en **otro** catálogo → colisión cross-marca: no se fusiona (regla 4 de producto).
     Como el `nombre` es único global, **no se puede insertar**: el producto se reporta en
     `report['blocked']` (o `skipped`) con motivo `'nombre colisiona con otra marca'` y
     **no se persiste**. Queda en el reporte de la corrida para que el superusuario lo revise.
3. **Vitales con tolerancia, acotado a la marca**: mismo `catalog_id`, compara los vitales
   del `kind` (panel: power+voc+vmp+imp; inverter: power+vmax) dentro de tolerancia → `update`.
   El equipo scrapeado puede traer un **nombre totalmente distinto** y aun así ser el mismo
   producto; por eso el match por vitales es imprescindible (el `unique` de `nombre` no lo
   detecta). En este caso **sobrevive el `nombre` original** del equipo existente: el upsert
   actualiza los demás campos pero **no pisa `nombre`** (ni `external_id`/`source` si se
   decide preservar la procedencia original; como mínimo `nombre`).
4. `is_locked` → `skip` (intacto).

> Implementación del upsert: el `_upsert` debe registrar **por qué** matcheó. Si el match fue
> por vitales (nombres distintos), se excluye `nombre` del conjunto de campos que se escriben
> sobre la fila existente. En matches por `external_id` o por nombre exacto/normalizado, los
> nombres ya coinciden, así que no hay nombre que preservar.

## 6. Visibilidad: ocultar catálogos inactivos a usuarios

Filtrar `is_active == True` en el cuello de botella de `CatalogService`:

- `own_catalog_ids`, `subscribed_catalog_ids`, `library`, `marketplace`, `bootstrap_org`.
- `deleted_library` no se toca (la papelera es papelera).
- `resolve_target_catalog` / `ensure_default_catalog`: los catálogos de workspace nacen
  `is_active=True`; no cambia su comportamiento.

Como toda la visibilidad fluye por estos métodos, las ~rutas que consumen `visible_catalog_ids`
(crud, projects, main, analysis_service) respetan el filtro automáticamente, sin tocarlas.

## 7. Centralización de catálogos oficiales (`CatalogService`)

Hoy `_official_catalog` está duplicado en `scrapers/service.py` y `utils/data_loader.py` y
busca por `nombre`. Se centraliza:

`CatalogService.official_catalog(display_name, *, active) -> Catalog`:
- Busca por `scraper_name = normalize_brand(display_name)`.
- Si no existe, crea `org_id=None, is_official=True, is_active=active, scraper_name=..., nombre=display`.
- Scraper la llama con `active=False` (cuarentena). El data_loader/seed con `active=True`
  (datos curados de arranque siguen visibles).

Ambos call-sites pasan a usar este helper.

## 8. Superusuario: gestión de catálogos (`app/superadmin/`)

UI server-rendered, junto a `/equipment/review`, con IP allowlist + MFA + `SuperadminAudit`.
CRUD completo + activación + merge.

Rutas (en `app/superadmin/views.py`):

- `GET  /catalogs` — lista **todos** los catálogos (incluye inactivos), con filtros
  (activo/inactivo, oficial/workspace) y contadores de equipos.
- `GET  /catalogs/<id>` — detalle (equipos, provenance).
- `POST /catalogs` — crear (CRUD).
- `POST /catalogs/<id>/edit` — editar `nombre`, `descripcion`, `scraper_name`.
- `POST /catalogs/<id>/activate` — `is_active=True`.
- `POST /catalogs/<id>/deactivate` — `is_active=False`.
- `POST /catalogs/<id>/delete` — soft-delete (CRUD).
- `GET  /catalogs/<src>/merge?target=<id>` — **preview** del merge (ver 8.1).
- `POST /catalogs/<src>/merge` — ejecuta el merge con las resoluciones elegidas.

Cada acción mutadora escribe `SuperadminAudit(action, target=catalog:<id>, detail=...)`.

### 8.1 Merge B (origen) → A (destino), resolución 1 a 1

Lógica en un servicio dedicado (`app/superadmin/catalog_merge.py` o método de `CatalogService`):

**Preview** clasifica los equipos de B (paneles + inversores; baterías/wires también se
reasignan si existen) frente a A:

- **Sin conflicto**: equipo de B cuyo nombre no existe en A y sin candidato semántico →
  se moverá (`catalog_id = A`).
- **Conflicto semántico**: equipo de B con un candidato en A por nombre-similar o vitales
  dentro de tolerancia → se presenta par `(B.item, A.item)` con opción
  `[conservar A] [usar B]`.

**Ejecución** (con las decisiones del superusuario):

- Sin conflicto → `catalog_id = A`.
- Conflicto, `conservar A` → se descarta el equipo de B (borrar fila de B), A intacto.
- Conflicto, `usar B` → como el `nombre` es único global, se reemplaza: borrar la fila de A
  y mover la de B a A (o copiar campos de B sobre A respetando `is_locked`). Definir como
  "borrar A, mover B" para evitar tocar `is_locked`; si A está `is_locked`, se fuerza
  `conservar A` y se reporta.
- **Suscripciones**: `CatalogSubscription` de B → A respetando `uq_sub_org_catalog`
  (si la org ya está suscrita a A, se borra la de B en vez de duplicar).
- **Cierre**: B queda vacío → soft-delete de B (o hard-delete; se usa soft-delete por
  consistencia con el resto).
- Todo en una transacción; auditar resultado (movidos / descartados / reemplazados).

## 9. Tests

`tests/test_autosolar_scraper.py`:

- `brands.py`: `normalize_brand` (acentos, espacios, guiones), `deduce_brand`
  (atributo estructurado → marca nueva; título → marca conocida; nada → `(None, None)`).
- `parse()` sobre fixtures HTML guardados (`tests/fixtures/autosolar/panel.html`,
  `inverter.html`) → campos correctos; `requests.get` mockeado.
- Servicio: producto sin marca → `blocked` (no persiste); marca nueva → catálogo creado
  `is_active=False`; marca existente → enruta a su catálogo.
- Dedup: mismo-marca por nombre y por vitales → `update` (no duplica); mismo nombre, otra
  marca → no fusiona (reportado en `blocked`/`skipped`, sin persistir).
- Dedup por vitales con **nombre distinto**: producto scrapeado con nombre totalmente
  distinto pero vitales coincidentes (misma marca) → `update`, y **el `nombre` original se
  conserva** (no se pisa con el del scraper).
- Visibilidad: catálogo `is_active=False` no aparece en `library`/`marketplace`/
  `visible_catalog_ids`; sí aparece en la consulta del superadmin.
- Merge: preview clasifica sin-conflicto vs conflicto; ejecución `conservar A` / `usar B`;
  dedup de suscripciones; B soft-deleted; `SuperadminAudit` registrado.
- No-regresión: Fronius sigue funcionando (resuelve catálogo por `scraper_name`).

## 10. Restricciones de implementación

- **Sin comentarios en el código** (preferencia inviolable de David). Toda explicación va en
  docstrings de módulo/función al estilo del repo, no en comentarios inline.
- Seguir patrones existentes (estructura de scrapers, blueprints, `SuperadminAudit`, estilo
  de migraciones linealizadas).
- Trabajo en **rama nueva** de feature; no tocar `main`.

## 11. Fuera de alcance

- Baterías y wires desde Autosolar (solo se reasignan en merge si existen).
- Descarga/parseo de PDF de datasheets para completar vitales de paneles.
- Programación/cron del scraper (sigue siendo CLI manual).
- UI React para gestión de catálogos (se usa el panel server-rendered).

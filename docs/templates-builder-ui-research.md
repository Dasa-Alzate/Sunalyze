# Constructor de plantillas — investigación y plan (feature-report-templates)

## Contexto del backend (autoridad)

### Gramática de expresiones `{{ ... }}`
- Placeholder: `re.compile(r'\{\{(.*?)\}\}', re.DOTALL)` (`parser.py`). Delimitadores `{{` `}}` deben estar balanceados; el interior se tokeniza.
- Tokenizer (`tokenizer.py`):
  - `MAX_EXPRESSION_LENGTH = 500`.
  - Identificador/ruta: `[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*`.
  - `_reject_unsafe_name`: cada segmento (split por `.`) NO puede empezar por `_` ni contener `__`. Rechaza dunders y guion bajo inicial.
  - Tokens: number, string (`'...'`/`"..."`), name, pipe `|`, op `+ - * /`, parens, comma.
- Parser: pipeline `base ( '|' filtro ('(' args ')')? )*`. Base vacía o expresión vacía => error.
- Filtros (`filters.py`), aridad:
  - `number(decimals=2)` — 0..1 args numéricos.
  - `thousands(decimals=2)` — 0..1 args numéricos.
  - `ellipsis(max_length)` — 1 arg requerido.
  - `upper()` — 0 args.
  - `lower()` — 0 args.
  - Nombre de filtro desconocido => `Filtro desconocido`.

### El cliente es SOLO UX
El backend valida al guardar vía `validate_content` (`saveContent`). El validador cliente
es feedback inmediato: NO ejecuta expresiones, NO resuelve variables, NO duplica la seguridad
(la frontera real de seguridad —rechazo de dunders en el resolver, ausencia de eval— sigue en
el backend). El cliente solo reproduce la gramática superficial para señalar errores antes de
guardar. Si el cliente pasara algo inseguro, el backend igualmente lo rechaza.

### Endpoints PDF (recién añadidos)
- `POST /api/templates/<id>/generate` body `{project_id}` => 201, `GeneratedDocument.to_dict()`. Permiso `template:manage`.
- `GET /api/projects/<project_id>/documents` => lista de documentos. Permiso `template:view`.
- `GET /api/documents/<doc_id>/download` => `application/pdf`, `Content-Disposition: attachment`. Permiso `template:view`.

Campos de `GeneratedDocument.to_dict()`: `id, project_id, template_id, template_version,
template_name, kind, pdf_sha256, pdf_size_bytes, status, generated_by_name, generated_at,
created_at`.

### Autorización
- `template:view` (member+), `template:manage` (admin/owner).
- Frontend: `useAuth().can('template:manage')` (AuthProvider expone `permissions` y `can`).

## Endpoints en `api.templates` (client.js)
Ya: setCategory, setLabels, categories, createCategory, removeCategory, labels, createLabel.
Faltan (añadir, mismo estilo, descarga como blob): `generate`, `projectDocuments`,
`downloadDocument`.

## Plan de implementación

### PIEZA 1 — Asignación de categoría/labels + crear (TemplatesGallery)
- Nuevo `AssignTemplateDialog.jsx` (Scrim): selección única de categoría (radios/select plano),
  multi de labels (checkboxes). Botones para crear categoría/label inline (createCategory/
  createLabel) que refrescan listas y filtros. Guarda con setCategory/setLabels.
- TemplateCard (tab Biblioteca): botón "Organizar" que abre el diálogo para esa instalación.
  Tras guardar, recargar biblioteca + categorías/labels.

### PIEZA 2 — Validación inline (TemplateBuilder)
- Nuevo `expressionValidator.js`: `validateBody(text) -> [{ expr, start, end, message }]`.
  Reproduce: balance de `{{ }}`, expresión no vacía, tokenización ligera, rechazo `_`/`__`,
  filtros conocidos con aridad. Devuelve lista de errores por posición.
- En cada sección, una lista de errores bajo el textarea (`role="alert"`/lista) con la expresión
  ofensiva y su posición; el textarea marca `aria-invalid`. Sin overlay (textareas no resaltan):
  lista de errores accesible.

### PIEZA 3 — Generar/descargar PDF
- `api.templates.generate`, `projectDocuments`, `downloadDocument` (blob).
- Nuevo `ProjectDocuments.jsx`: selector de proyecto (como LivePreview), botón "Generar PDF"
  (solo con `template:manage`), lista de documentos con versión/fecha/tamaño y botón "Descargar".
- Integrado en TemplateBuilder bajo el LivePreview (o sección propia).

### Tests
- `expressionValidator.test.js`: válida vs dunder vs filtro desconocido vs aridad.
- Extender `templates.test.jsx`: axe de AssignTemplateDialog y ProjectDocuments.
- Mantener verdes los 60 previos.

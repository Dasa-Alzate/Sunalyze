# Enganche a PDF de plantillas: GeneratedDocument

## Objetivo
Renderizar una plantilla (version fijada) + un proyecto a PDF con WeasyPrint y
persistir el artefacto con un registro `GeneratedDocument` org-scoped.

## Hechos del codigo existente
- `MemoriaService.generar_pdf` usa `from weasyprint import HTML` (import diferido) y
  `HTML(string=html_string).write_pdf()`. Reusamos ese pipeline.
- `renderer.render_version(version_content, project, user, org, on_error)` devuelve
  `{'sections': [...], 'html': '...'}`; `html` ya ensambla las secciones en
  `<section>` con `<h2>` y `<div class="tpl-body">`. Falta envolverlo en una pagina
  imprimible (doctype, `<html><head><style>`, margenes `@page`).
- `LegalizationService.hash_pdf` = `hashlib.sha256(pdf_bytes).hexdigest()`. Mismo patron.
- `MemoriaSignature` fija `pdf_sha256` (String 64) y `pdf_size_bytes` (Integer). Espejo.
- Modelos heredan `BaseModel` (id, created_at, updated_at). `instance/` esta gitignored.
- Head de migraciones actual: `293a01810210`.
- `TemplateService._accessible_template(org_id, id)` y validacion de proyecto por
  `project.org_id == org_id` (NotFound si ajeno) ya implementan el patron anti-IDOR.
- Permisos: `TEMPLATE_VIEW` (lectura), `TEMPLATE_MANAGE` (escritura/generar).
- Rutas siempre tras `@require_flag('templates')` + `@require_permission(...)`.

## Decisiones
- `GeneratedDocument` vive en `app/models/report_template.py` (donde estaba la nota TODO).
  Campos: org_id, project_id (FK), template_id (FK), template_version_id (FK, version
  FIJADA), kind, pdf_path, pdf_sha256, pdf_size_bytes, status, generated_by (FK user),
  generated_at. Relaciones a Project, ReportTemplate, TemplateVersion.
- Version fijada: el servicio elige `published_version or latest_version` y guarda su id
  en `template_version_id`; el render usa el `content` de ESA version.
- Persistencia: bytes a `<instance>/generated/<org_id>/<uuid>.pdf` (gitignored). `pdf_path`
  guarda la ruta relativa a `instance_path` para portabilidad.
- Servicio nuevo `app/services/document_service.py` (dominio puro). Envuelve el HTML de
  secciones en un documento imprimible minimo y llama WeasyPrint con import diferido.
- Rutas: `POST /api/templates/<id>/generate` (TEMPLATE_MANAGE),
  `GET /api/projects/<project_id>/documents` (TEMPLATE_VIEW),
  `GET /api/documents/<doc_id>/download` (TEMPLATE_VIEW, stream application/pdf).
- Schema `GenerateSchema(project_id: int)`.
- Migracion batch-safe, server_default en NOT NULL, down_revision=293a01810210.
- WeasyPrint puede fallar por libs nativas (Pango) en local: el servicio aisla el paso
  `write_pdf`; los tests degradan a verificar HTML+modelo+wiring si falta la lib nativa.

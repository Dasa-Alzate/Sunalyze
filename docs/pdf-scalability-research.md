# PDF scalability — investigación y plan (auditoría #5 + #6)

## Problemas
- **#5 (worker blocking / DoS):** `DocumentService.generate` y `MemoriaService.generar_pdf`
  renderizan el PDF con WeasyPrint de forma **síncrona dentro del request**, sin cola ni
  rate-limit. Un pico de peticiones bloquea los workers de gunicorn (`--timeout 120`,
  `--workers 2`).
- **#6 (filesystem local):** los PDFs persistidos se guardan en
  `instance/generated/<org_id>/<uuid>.pdf` (ver `DocumentService._persist_pdf` /
  `_generated_dir` / `read_pdf_bytes`), lo que rompe despliegues multi-instancia/Docker donde
  el disco no es compartido.

## Estado actual (hechos del código)
- `DocumentService.generate(org_id, template_id, project_id, user)` → renderiza, escribe el
  fichero con `open(...,'wb')`, crea `GeneratedDocument(pdf_path=relpath, pdf_sha256, ...)`,
  commit, devuelve el modelo. Ruta: `POST /api/templates/<id>/generate` → **201 + doc.to_dict()**.
- `DocumentService.read_pdf_bytes` valida propiedad por org (`_owned_document` → NotFound en
  IDOR) y lee el fichero (`NotFound` si falta). Ruta: `GET /api/documents/<id>/download`.
- `MemoriaService.generar_pdf(form_data)` → devuelve **bytes** del PDF (no persiste). Ruta:
  `GET|POST /imprimir/memoria-pdf` → **inline application/pdf**.
- `GeneratedDocument.pdf_path` (String 500) guarda la ref relativa a `instance_path`.
- `limiter` (flask-limiter) es singleton en `app/extensions.py`, inicializado en
  `security_headers.register_security`; patrón `@limiter.limit('N per unit')` ya usado en
  `auth.py` / `emails.py` / `superadmin`.
- Deps: `redis` (cliente) ya está en requirements; **`boto3` y `rq` NO** están instalados.
- `weasyprint` está instalado en el venv → los tests de generación real corren.

## Diseño (dos abstracciones + adaptadores swappable)

### StorageGateway (`app/gateways/storage/`)
Interfaz: `save(org_id, key, data: bytes) -> ref`, `read(ref) -> bytes`, `exists(ref) -> bool`,
`url(ref) -> str | None`.
- **LocalStorage (DEFAULT):** replica EXACTO el layout actual —
  `instance/generated/<org_id>/<key>`; `ref` = ruta relativa a `instance_path`
  (idéntico a `pdf_path` de hoy). `read`/`exists` resuelven contra `instance_path`.
- **S3Storage:** compatible S3/MinIO; `import boto3` **perezoso** dentro de los métodos;
  objeto en `<prefix>/<org_id>/<key>`; `url` = presigned GET.
- Selección: `get_storage()` lee `STORAGE_BACKEND` (`local`|`s3`).

### JobQueue (`app/gateways/queue/`)
Interfaz: `enqueue(job_name, **kwargs) -> job_id`, `get_status(job_id) -> str`,
`get_result(job_id)`, propiedad `is_async`.
- **SyncQueue (DEFAULT):** ejecuta el job **inline** al hacer `enqueue`, guarda el resultado
  (dict/bytes) y lo devuelve por `get_result`. Las excepciones **propagan** (mismo contrato de
  error que hoy). `is_async = False`.
- **RQQueue:** `import rq`/`redis` **perezoso**; encola en Redis; `is_async = True`;
  `job_timeout` configurable.
- Registro de jobs en `app/jobs/` (nombre → callable) para que ambos adaptadores despachen
  con funciones importables (requisito de RQ).
- Selección: `get_queue()` lee `JOB_QUEUE` (`sync`|`rq`).

### Endpoints
- `POST /api/templates/<id>/generate`: pasa por `enqueue('generate_document', ...)`.
  - sync (default) → `get_result` inmediato → **201 + doc dict** (sin regresión).
  - async → **202 + {job_id, status}**; polling en `GET /api/documents/jobs/<job_id>`
    (verifica `org_id` del resultado; 404 si ajeno). Descarga sigue por
    `/api/documents/<id>/download` (ahora lee vía StorageGateway).
- `GET|POST /imprimir/memoria-pdf`: pasa por `enqueue('memoria_pdf', ...)`.
  - sync (default) → `get_result` (bytes) → **inline application/pdf** (sin regresión, sin
    escribir a disco).
  - async → **202 + {job_id}**; polling en `GET /api/memoria/jobs/<job_id>` que devuelve
    **202 {status}** hasta terminar y luego **200 application/pdf** con los bytes del resultado.
- `@limiter.limit(PDF_RATELIMIT)` en AMBOS endpoints de generación SIEMPRE (sync o async).

### Esquema
Cambio **mínimo: ninguno**. `pdf_path` sigue guardando la `ref` del backend activo (para local
es idéntico a hoy). Documentado: cambiar de backend no migra artefactos previos. (La columna
`storage_backend`/`storage_key` queda descartada por preferir el esquema mínimo y evitar
riesgo de migración; único head alembic intacto.)

## No-regresión (defaults local + sync)
Mismos endpoints, mismas respuestas (201 doc / inline bytes), PDFs en el mismo sitio,
`GeneratedDocument`/`pdf_sha256` idénticos. La suite existente sigue verde sin cambiar
expectativas. La app arranca sin `boto3`/`rq` (imports perezosos).

## Config (env)
- `STORAGE_BACKEND=local|s3` (default `local`)
- `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_PREFIX`,
  `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (o `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY`)
- `JOB_QUEUE=sync|rq` (default `sync`)
- `JOB_QUEUE_REDIS_URL` (o `REDIS_URL`), `JOB_QUEUE_NAME` (default `pdf`), `PDF_JOB_TIMEOUT`
- `PDF_RATELIMIT` (default `60 per hour`)
- `boto3` y `rq` quedan como **extras opcionales** (no dependencia dura).
</content>

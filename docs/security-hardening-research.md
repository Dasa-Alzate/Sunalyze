# Endurecimiento de seguridad (auditoria 2026-07-07)

Entregable de investigacion/analisis. Recoge las decisiones de diseno por hallazgo,
la normativa aplicable y los puntos de integracion. Un commit atomico por hallazgo.

Base: `main` @ 9e8652f. Head alembic previo: `c5d6e7f8a9b0` (unico head; verificado).

## Alto

### #1 SSRF/LFI via `logo_path` en el render de PDF
WeasyPrint resuelve y descarga cada recurso referenciado en el HTML (p. ej. `<img src>`).
Con `logo_path` bajo control del usuario, un `http(s)://` interno permite SSRF y un
`file://` permite LFI. Defensa doble:

- **url_fetcher restringido** (`app/services/pdf_url_fetcher.py`): solo permite `data:` y
  ficheros locales cuyo `realpath` cae bajo `current_app.instance_path`. Rechaza
  `http/https/ftp/...` y cualquier ruta fuera del arbol permitido. Se cablea en las dos
  llamadas `HTML(...)`: `document_service._render_pdf` y `memoria_service.generar_pdf`
  (con `base_url=instance_path` para que las rutas relativas resuelvan dentro del arbol).
- **Validacion de `logo_path`** (`schemas/org.py`): ruta relativa segura (sin esquema, sin
  `..`, sin ser absoluta, sin backslashes). El docstring de `organization.py:46` ya fija que
  `logo_path` es relativa a `instance_path`.

### #2 Revocacion de sesion al cambiar contrasena
Sesiones stateless (cookie firmada). Se anade `session_gen` (entero, `server_default '0'`) a
`User`. `login_user` graba `session['session_gen']` con el valor vigente; `current_user()` exige
que coincida con `user.session_gen`. `set_password` incrementa `session_gen`, de modo que
reset y cualquier cambio de contrasena (y `anonymize`) invalidan TODAS las sesiones previas.

Decision: el reset de contrasena NO es un flujo autenticado (se llega por enlace de correo,
sin sesion activa del actor), asi que no hay sesion propia que preservar: se rota y mueren
todas las cookies anteriores. En registro, `set_password` corre antes de `login_user`, de modo
que la sesion recien emitida ya lleva el `session_gen` correcto. Tras el deploy, las cookies
previas (sin `session_gen`) dejan de validar: re-login unico y esperado.

Migracion: `add_column` con `server_default='0'` (batch-safe, seguro en tablas con filas),
`down_revision = c5d6e7f8a9b0`, head unico.

## Medio

### #3 Path traversal en datasheets
`_collect_datasheets`/`_merge_pdfs` construyen la ruta a partir de `device.datasheet`. Se anade
`_safe_datasheet_path`: rechaza separadores y `..`, y exige
`realpath(path).startswith(realpath(DATASHEETS_DIR)+os.sep)` antes de `pikepdf.open`.

### #4 IDOR del job de la memoria PDF
El job de memoria devolvia bytes crudos, sin dueno. Ahora `memoria_pdf_job` recibe `org_id`
(y `user_id`) al encolar y devuelve `{'org_id', 'pdf'}`. La ruta de estado rechaza con 404 si
`result['org_id'] != current_org_id()`, replicando el patron correcto de
`routes/templates.py:163-165`.

### #5 Lockout en el login de superadmin
El login de superadmin no aplicaba lockout. Se reusa `is_locked_out`/`register_failed_login`/
`register_successful_login` del modelo `User` (mismo mecanismo que `AuthService.authenticate`).

### #6 Rate-limit
`@limiter.limit` en `reset-password` y `verify-email` (10/hora/IP) y en `panel-analysis`/
`diagrama-completo` (120/hora, configurable por `ANALYSIS_RATELIMIT`). `forgot-password` ya
tenia 5/min. Tests de auth desactivan el limiter (`RATELIMIT_ENABLED=False`).

### #7 Token de reset de un solo uso
El payload del token de reset incluye una huella del `password_hash` actual
(`sha256(password_hash)[:16]`). `reset_password` la recomputa y compara: al cambiar la
contrasena la huella cambia y el token muere; ademas no se puede reutilizar.

### #8 Redis con password
`docker-compose.yml`: `redis-server --requirepass ${REDIS_PASSWORD:?...}` y password en
`CACHE_REDIS_URL`/`RATELIMIT_STORAGE_URI`/`JOB_QUEUE_REDIS_URL`. `REDIS_PASSWORD` en
`.env.docker.example`. Puertos sin publicar. Arranque local sin Redis intacto (defaults a
memoria/SimpleCache).

## Bajo

- **#10** Open redirect en `_finish_login` del superadmin: acepta `next` solo si
  `urlparse(next).netloc == ''` y empieza por `/`.
- **#12** `MAX_CONTENT_LENGTH = 16 MB` en `config.py`.
- **#13** `primary_color` validado con `^#[0-9a-fA-F]{3,8}$` en `schemas/org.py`.
- **#14** `run.py`: `debug` desde `FLASK_DEBUG`.
- **#15** `MFA_ENC_KEY` exigida en produccion (`FLASK_ENV=production`); fuera de prod se
  mantiene el fallback derivado de `SECRET_KEY`.

## Deferidos (no se tocan)
- **#9** enumeracion por timing (decision con matiz).
- **#11** XFF (mitigado por publicar en loopback segun la guia).
- **#16** bump de Flask 3.x/Vite (tarea aparte, mas arriesgada).

## Tests existentes actualizados (mantenimiento, no desarrollo)
- `test_auth_flows.py::PasswordResetTest::test_reset_token_is_reusable_while_valid` fijaba el
  comportamiento inseguro (token reutilizable). Tras #7 se renombra/reescribe para exigir que
  el segundo uso del mismo token sea rechazado (token muere al cambiar el hash).

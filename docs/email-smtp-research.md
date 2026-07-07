# Envío real de email por SMTP genérico — investigación

## Problema (auditoría #8, bloqueante nº1 de producción)

`EmailService.send` (`app/services/email_service.py`) renderiza la plantilla y **solo
loguea**: devuelve `{'sent': False, 'reason': 'SMTP no configurado (dev)'}`. Los correos de
bienvenida/verificación (`auth.register`), reset de contraseña (`auth.forgot_password`),
invitaciones (`members.create_invitation`) y el envío manual de superadmin
(`emails.send_email`) no se entregan nunca.

## Interfaz actual (a respetar sin tocar llamadores)

- `EmailService.send(template_id, to, context=None, locale=None)` → dict
  `{'sent': bool, 'to': str, 'subject': str, 'locale': str, 'reason'?: str}`.
- No hay campo `body` texto: los correos son HTML renderizado con Jinja
  (`templates/emails/<locale>/<archivo>`); el asunto sale de `SUBJECTS` por locale.
- Contrato blando: `send` no lanza si el envío falla; los llamadores (registro, reset,
  invitación) siguen su flujo. `KeyError` sí propaga para plantilla desconocida
  (los llamadores del endpoint lo convierten en 404) — se mantiene.
- Tests existentes que dependen del comportamiento:
  - `tests/test_emails_security.py::test_superadmin_send_is_allowed` asume `sent == False`
    (válido mientras el backend de test sea `log`).
  - `tests/test_i18n_integration.py::test_recipient_locale_used` asume que `send` devuelve
    `locale`.

## Patrón del repo para backends intercambiables

`app/gateways/storage/` y `app/gateways/queue/`: paquete con `base.py` (contrato +
excepción propia), un adaptador por backend, y `__init__.py` con `get_*()` que lee
`current_app.config` y hace import perezoso del adaptador pesado. La config vive en
`config.py` como atributos de `Config` leídos de entorno, con default seguro.
`config.py` ya falla alto en arranque ante configuración inválida
(`_resolve_database_url`, `_resolve_secret_key`).

## SMTP con stdlib (sin dependencias nuevas)

- `smtplib.SMTP(host, port, timeout=...)` como context manager cierra la conexión (QUIT)
  incluso ante excepción.
- STARTTLS (puerto 587, el estándar de envío autenticado hoy): `smtp.starttls()` antes de
  `login()`; `ssl.create_default_context()` es el default implícito en Python ≥3.10 y valida
  certificado y hostname.
- `email.message.EmailMessage` + `msg.set_content(html, subtype='html')` construye un
  mensaje HTML correcto (MIME, charset UTF-8, cabeceras `From`/`To`/`Subject` con RFC 2047
  para no-ASCII). `smtp.send_message(msg)` deriva envelope from/to de las cabeceras.
- Jerarquía de errores: `smtplib.SMTPException` cubre auth, recipients rechazados, datos…
  pero los fallos de red/DNS/timeout llegan como `OSError` (`socket.timeout` es subclase).
  Capturar `(OSError, smtplib.SMTPException)`.
- Funciona igual contra SES-SMTP, Brevo, Mailgun, Gmail, etc.: todos exponen endpoint
  SMTP con STARTTLS en 587 y auth usuario/contraseña.

## Decisiones

1. **`MAIL_BACKEND=log|smtp`, default `log`**: cero regresión; dev y tests siguen igual.
2. **Backend desconocido → `RuntimeError` en arranque** (no fallback silencioso a `log`):
   un typo como `MAIL_BACKEND=smpt` que degradase a `log` reproduciría en producción el
   mismo bug que esta feature corrige (correos que "se envían" pero nunca salen). Coherente
   con cómo `config.py` ya trata `DATABASE_URL`/`SECRET_KEY` inválidas.
3. **Con `MAIL_BACKEND=smtp`, `MAIL_SMTP_HOST` y `MAIL_FROM` son obligatorios en arranque**
   por la misma razón: sin host o sin remitente todo envío fallaría en runtime de forma
   silenciosa (contrato blando).
4. **Fallo SMTP no propaga**: `EmailService.send` captura la excepción del adaptador,
   `logger.error` con contexto (backend, destinatario, plantilla) y devuelve
   `{'sent': False, 'reason': ...}`. Si Sentry está activo, `logger.error` ya se captura
   como evento vía su integración de logging.
5. **HTML single-part**: las plantillas son HTML; no se fabrica alternativa de texto plano
   (fuera de alcance, ningún llamador la aporta hoy).

## Config nueva (`config.py`)

| Variable | Default | Uso |
|---|---|---|
| `MAIL_BACKEND` | `log` | `log` o `smtp`; otro valor rompe el arranque |
| `MAIL_SMTP_HOST` | — | obligatoria con backend `smtp` |
| `MAIL_SMTP_PORT` | `587` | puerto de envío |
| `MAIL_SMTP_USERNAME` | vacío | si vacío no se hace `login()` |
| `MAIL_SMTP_PASSWORD` | vacío | credencial del `login()` |
| `MAIL_SMTP_STARTTLS` | `true` | `starttls()` antes de auth |
| `MAIL_FROM` | — | remitente; obligatoria con backend `smtp` |
| `MAIL_TIMEOUT` | `10` | segundos de timeout de socket |

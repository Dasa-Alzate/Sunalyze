# Auth flow tests — research (hallazgo de auditoría #9)

## Contexto del hallazgo
Los tests existentes saltan el login real: `_login` escribe `sess['user_id']`/`sess['org_id']`
directo en la sesión (`tests/test_rbac_denial.py:72`, mismo patrón en gdpr/workspace/admin),
y todos crean la app con `WTF_CSRF_ENABLED=False`. Registro, verify-email, login, logout,
forgot/reset y CSRF tenían cero cobertura extremo a extremo.

## Mapa del sistema de autenticación

### Rutas (`app/routes/auth.py`)
- `POST /api/auth/register` — `@limiter.limit('10 per hour')`. Valida con `RegisterSchema`,
  llama `AuthService.register`, envía email `welcome` con `cta_url = /verificar?token=...`,
  hace `login_user(user)` (sesión inmediata, ANTES de verificar el correo) y devuelve 201
  con `verify_link` en dev (`IS_PRODUCTION=False`).
- `POST /api/auth/login` — `@limiter.limit('10 per minute')`. `AuthService.authenticate` +
  `login_user(user, remember=data.remember)`.
- `POST /api/auth/logout` — sin `login_required`; `session.clear()`; idempotente.
- `GET /api/auth/me` — payload de sesión (user None si no hay sesión), sin auth.
- `POST /api/auth/forgot-password` — `@limiter.limit('5 per minute')`. Respuesta genérica
  siempre (anti-enumeración); email `reset-password` solo si el usuario existe;
  `reset_link` en dev.
- `POST /api/auth/reset-password` y `POST /api/auth/verify-email` — sin rate limit propio.

### Dominio (`app/services/auth_service.py`)
- `register`: email lower/strip, `Conflict 409 auth.email_taken` si duplicado. Sin company →
  org PERSONAL "Mi espacio" seats=1; con company → org BUSINESS seats=5. Membership `owner`.
  `CatalogService.bootstrap_org` (suscripciones locales, sin red). Token verify vía
  `tokens.issue(VERIFY_EMAIL, {'uid': user.id})`.
- `authenticate`: lockout primero (`Forbidden 403 auth.account_locked` incluso con password
  correcta); credenciales malas → `Unauthorized 401 auth.invalid_credentials` con mensaje
  único "Correo o contraseña incorrectos." (no filtra qué campo). Éxito resetea contadores,
  registra `auth.login` en audit.
- `reset_password`: `tokens.verify(RESET_PASSWORD, max_age=3600)`; `verify_email`:
  `max_age=86400` → marca `email_verified=True`.

### Tokens (`app/gateways/tokens.py`)
`itsdangerous.URLSafeTimedSerializer(SECRET_KEY, salt=<propósito>)`. **Stateless**: no hay
tabla de tokens ni marca de "usado". Expirado → `ValidationError 422 token.expired`;
manipulado → `422 token.invalid`. El salt separa propósitos (un token de verify no vale
para reset). Consecuencia: un token de reset es REUTILIZABLE durante su hora de vida y no
se invalida al cambiar la contraseña (payload = solo `{'uid': id}`).

### Lockout (`app/models/user.py`, migración c7f602e8e288)
`FAILED_LOGIN_THRESHOLD=5`, ventana y bloqueo de 15 min (`LOGIN_ATTEMPT_WINDOW`,
`LOCKOUT_DURATION`). `register_failed_login` reinicia el contador si el último fallo es
más viejo que la ventana; al 5º fallo fija `lockout_until`. Independiente del rate limit.

### Política de contraseña (`app/schemas/auth.py`)
OWASP ASVS: min 12, max 128, lista local de contraseñas filtradas, rechazo de baja
diversidad (`len(set) <= 2`). Aplica en `RegisterSchema` y `ResetSchema`. Errores pydantic
→ handler central 422 `error.validation` con `details[{field,msg}]`.

### CSRF (`app/security_headers.py`, `app/extensions.py`)
Flask-WTF `CSRFProtect` global (protege todo método mutador). Patrón double-submit para la
SPA: cada respuesta setea cookie `csrf_token` (no HttpOnly) con `generate_csrf()`; la SPA
la lee y la devuelve en la cabecera `X-CSRFToken` (default de Flask-WTF junto a
`X-CSRF-Token`). La validación compara contra el token crudo guardado en la sesión firmada.
Fallo → handler `CSRFError` → 403 JSON `{'error': 'Token CSRF inválido o ausente. Recarga
la página.'}` (el error visto en prod). Ningún endpoint de API usa `csrf.exempt`.

### Rate limiting
`Flask-Limiter` sin límites por defecto (`default_limits=[]`); solo los decoradores de auth.
Storage `memory://`. Se desactiva por app de test con `RATELIMIT_ENABLED=False` en los
overrides de `create_app` (Flask-Limiter lo lee en `init_app`).

### Email
`EmailService.send` renderiza Jinja y delega en `get_mailer()` (`MAIL_BACKEND=log` default:
solo loguea, jamás SMTP). Contrato blando: nunca propaga fallos. Capturable con
`mock.patch.object(EmailService, 'send')`; el token viaja en `context['cta_url']` /
`context['reset_url']` / `context['accept_url']`.

### Verificación de email: comportamiento real
`email_verified` NO se consulta en ninguna ruta, decorador ni servicio (`grep` sobre
`app/routes`, `app/authz.py`, `app/services`): una cuenta sin verificar opera con todos
sus permisos, y `register` inicia sesión antes de verificar. Es una decisión de producto
implícita; los tests la documentan como contrato observado.

### Invitaciones (`app/routes/members.py`, `app/services/membership_service.py`)
`POST /api/invitations` requiere `Permission.MEMBER_INVITE`; token opaco de 32 bytes en BD.
`POST /api/invitations/<token>/accept` (`login_required`) crea Membership con el rol de la
invitación y cambia el workspace activo. Token inexistente → 404 `invitation.not_found`;
re-aceptar → 409.

## Cobertura previa (no duplicar)
- `test_rbac_denial.py`: matriz 403 por rol member, 401 sin sesión en 7 endpoints, gate
  superadmin de `/api/admin/*`.
- `test_admin_ip_gate.py`: allowlist IP de admin. `test_gdpr.py`: export/erasure.
- `test_workspace_switch.py`: switch multi-org, IDOR→404.
Todos con inyección de sesión y CSRF off — exactamente el hueco a rellenar.

## Plan (análisis)
Un solo archivo `tests/test_auth_flows.py` reusando el harness de la suite (unittest,
`create_app` con sqlite en memoria, `db.create_all`, subTests):
1. `RegistrationFlowTest` — alta ok (personal y business), password débil parametrizada,
   duplicado (case-insensitive), email de verificación capturado + token funcional,
   sesión inmediata post-registro.
2. `EmailVerificationTest` — token válido/ inválido/ caducado (emisión con `time.time`
   parcheado), login sin verificar (comportamiento real).
3. `LoginLogoutTest` — sesión funcional post-login, 401 idéntico para email inexistente y
   password mala, `remember` (cookie con/sin Expires), logout invalida, lockout a los 5
   fallos incluso con password correcta.
4. `PasswordResetTest` — forgot dispara email con token (y anti-enumeración), reset cambia
   la password efectiva, política min 12, token inválido/caducado, reuso (documenta el
   comportamiento real stateless).
5. `CsrfContractTest` — app con `WTF_CSRF_ENABLED=True`: mutación sin token → 403 con el
   mensaje exacto de prod; con token obtenido por el mecanismo real de la SPA (cookie
   `csrf_token` → cabecera `X-CSRFToken`) → pasa; token corrupto → 403.
6. `InvitationAuthTest` — invitar+aceptar por HTTP real crea membership con rol, token
   inválido → 404, sin sesión → 401.
Emails siempre capturados con mock del `EmailService.send` (backend jamás tocado).

## Hallazgo sobre el harness (descubierto al ejecutar)
El patrón de la suite (mantener `app.app_context()` empujado durante todo el test) hace
que Flask REUTILICE ese contexto en cada request del test client, de modo que `g`
sobrevive entre requests: Flask-WTF cachea el token CSRF firmado en `g.csrf_token` y
`authz.current_role` cachea `g._role`. Con CSRF activado, el ciclo
register→logout→login da un 403 espurio, y tras aceptar una invitación el rol devuelto
es el rancio — comportamientos que NO ocurren en producción (cada request tiene `g`
fresco). Por eso `test_auth_flows.py` no comparte contexto con los requests y abre
`app_context` puntuales para BD/tokens; sqlite en memoria persiste entre contextos por
el StaticPool de Flask-SQLAlchemy. No es un bug de la app; sí es una trampa a conocer
si otra suite activa CSRF o testea cambios de rol multi-request con el harness clásico.

Segunda trampa: `limiter` (Flask-Limiter) es un singleton de módulo compartido entre
apps; `RATELIMIT_ENABLED=False` en `init_app` fija `limiter.enabled=False` para TODO el
proceso (rompía `test_health_observability` al correr después). `test_auth_flows.py` lo
restaura con `addCleanup`.

# Investigacion: endurecimiento de cuentas + fundacion de auditoria

Entregable del paso 1 (investigacion) de la feature 12. Recoge la normativa
aplicable, las decisiones de dominio y los parametros elegidos.

## 1. Endurecimiento de autenticacion (OWASP ASVS 4.0, V2)

### Anti-automatizacion y lockout (ASVS 2.2.1)

> "Verify that anti-automation controls are effective at mitigating breached
> credential testing, brute force, and account lockout attacks. (...) Verify
> that no more than 100 failed attempts per hour is possible on a single
> account."

Controles aceptados: soft lockout, rate limiting, retrasos crecientes,
CAPTCHA, restricciones por IP. La guia de pruebas (WSTG) describe el bloqueo
tipico tras 3-5 intentos fallidos con desbloqueo por ventana temporal.

Riesgo conocido: un lockout mal disenado permite denegacion de servicio
(bloquear la cuenta de otro a base de intentos). Mitigaciones: ventana de
bloqueo corta con auto-expiracion (soft lockout), contar por cuenta y no
exponer si la cuenta existe.

### Fortaleza de contrasena (ASVS 2.1.x)

- 2.1.1: minimo 12 caracteres.
- 2.1.2: permitir al menos 64, denegar mas de 128.
- 2.1.9: sin reglas de composicion obligatorias (no forzar mayusculas/numeros).
- 2.1.7: comprobar contra contrasenas filtradas (local o API externa).

### Decisiones de dominio adoptadas

El esquema previo exigia 8 caracteres + letra + numero (regla de composicion,
contraria a 2.1.9). Se eleva a la **politica minima alineada con ASVS**:

- Longitud minima **12**, maxima **128** (2.1.1 / 2.1.2).
- Se elimina la regla de composicion letra+numero (2.1.9).
- Lista local de contrasenas triviales/filtradas mas comunes (subconjunto de
  2.1.7; sin dependencia externa nueva, solo stdlib). Rechazo de la contrasena
  igual a una entrada de la lista o que sea una sola repeticion trivial.

### Parametros de lockout elegidos

- **Umbral:** 5 intentos fallidos consecutivos (dentro de 3-5 recomendado por
  WSTG y por debajo del techo de 100/h de 2.2.1).
- **Ventana de conteo:** 15 minutos. Intentos fallidos mas antiguos que la
  ventana no cuentan (soft lockout, mitiga DoS).
- **Duracion del bloqueo:** 15 minutos. Tras la ventana, el siguiente intento
  vuelve a permitirse.
- Un login correcto **resetea** el contador y limpia el bloqueo.
- Defensa en capas: el rate limit existente (`10 per minute` en `/login`) sigue
  activo por IP; el lockout actua por cuenta.

Implementacion: contador y marca de bloqueo en el modelo `User`
(`failed_login_count`, `lockout_until`, `last_failed_login_at`, `last_login_at`).
Se evita una tabla `LoginAttempt` por intento para no crecer sin control; el
soft lockout por ventana se consigue reseteando el contador cuando el ultimo
fallo es mas viejo que la ventana.

## 2. Fundacion de auditoria (append-only, org-scoped)

### Patrones de audit log

- **Append-only:** las filas no se actualizan ni se borran desde la aplicacion;
  solo se insertan. El servicio expone unicamente `record(...)` y lecturas.
- **Tamper-evidence (futuro):** hash-chaining (cada entrada incluye el SHA-256
  de la anterior) o arboles de Merkle dan deteccion de manipulacion. No se
  implementa ahora, pero el modelo reserva el campo `payload` (JSON) y un diseno
  estable de columnas para poder anadir una columna `prev_hash`/`entry_hash`
  sin migracion disruptiva.
- **Atomicidad:** la entrada de auditoria se escribe en la **misma transaccion**
  que la mutacion que describe (no en `after_request`). Asi, si la mutacion hace
  rollback, la auditoria tambien; nunca queda un evento "fantasma" ni se pierde
  uno por un fallo posterior del request. `AuditService.record(...)` hace
  `session.add(...)` y `flush()`, pero **no** `commit()`: el commit lo hace el
  llamador junto con su cambio.

### Modelo `AuditEvent`

Columnas: `actor_user_id`, `actor_email` (desnormalizado, sobrevive al borrado
del usuario), `org_id` (eje multi-tenant), `action`, `entity_type`, `entity_id`,
`payload` (Text con JSON: diff/contexto), `ip`. Hereda `BaseModel`
(`id`, `created_at`, `updated_at`); `created_at` es la marca temporal del evento.

Indices por `org_id` y por `(org_id, created_at)` para la lectura de la
bitacora de una org ordenada por fecha.

### Unificacion futura con `superadmin_audit`

El portal de superadmin (otra rama) tiene su propia `superadmin_audit`. Este
`AuditEvent` es la fundacion general. Para permitir unificar ambas en el futuro:

- `org_id` es **nullable**: los eventos de plataforma/superadmin (sin org)
  caben en la misma tabla.
- `actor_email` desnormalizado permite registrar actores que no son `User` de
  esta tabla (p. ej. superadmins en otro modelo).
- `action`/`entity_type` son strings libres con convencion `dominio.verbo`
  (p. ej. `auth.login`, `project.create`), espacio de nombres compartible.

## Fuentes

- OWASP ASVS 4.0 V2 Authentication:
  https://github.com/OWASP/ASVS/blob/master/4.0/en/0x11-V2-Authentication.md
- OWASP Authentication Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP WSTG, Testing for Weak Lock Out Mechanism:
  https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/03-Testing_for_Weak_Lock_Out_Mechanism
- OWASP Blocking Brute Force Attacks:
  https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks
- Immutable / append-only audit log patterns (hash-chaining, Merkle):
  https://www.designgurus.io/answers/detail/how-do-you-enforce-immutability-and-appendonly-audit-trails

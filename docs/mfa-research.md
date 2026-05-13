# MFA/2FA (TOTP) para el portal de superadmin — investigación

Entregable del paso 1 (investigación) de la feature. Recoge los hechos, fórmulas
y decisiones de dominio que sustentan la implementación con stdlib.

## TOTP = HOTP sobre el tiempo

- **HOTP (RFC 4226)**: HMAC-based One-Time Password. Genera un código a partir de
  un secreto compartido `K` y un contador `C` de 8 bytes big-endian:
  `HOTP(K, C) = Truncate(HMAC-SHA1(K, C))`.
- **TOTP (RFC 6238)**: HOTP donde el contador es el número de pasos de tiempo
  transcurridos: `T = floor((unixtime - T0) / X)`. Por defecto `T0 = 0` y
  `X = 30` segundos. El paso `T` se codifica como entero de 8 bytes big-endian y
  se alimenta a HOTP.

### Truncamiento dinámico (RFC 4226 §5.3)

Sobre el digest HMAC (20 bytes para SHA1):

1. `offset = digest[19] & 0x0f` (los 4 bits bajos del último byte).
2. Tomar 4 bytes desde `offset`, enmascarar el bit más alto:
   `bincode = (digest[offset] & 0x7f) << 24 | (digest[offset+1] & 0xff) << 16
   | (digest[offset+2] & 0xff) << 8 | (digest[offset+3] & 0xff)`.
3. `otp = bincode % 10**digits` (digits = 6).
4. Rellenar con ceros a la izquierda hasta `digits`.

### Algoritmo / dígitos / período

Los authenticators (Google Authenticator, Authy, 1Password, etc.) asumen por
defecto **SHA1, 6 dígitos, período 30 s**. Mantener estos valores maximiza la
compatibilidad; los parámetros no estándar (SHA256, 8 dígitos) muchos lectores
los ignoran. Implementación con `hmac` + `hashlib.sha1`.

### Ventana de tolerancia (clock skew)

El reloj del dispositivo del usuario y el del servidor pueden desfasar. Se
verifica el paso actual y los pasos vecinos. **Ventana ±1** = comprobar
`T-1, T, T+1` (cubre ~90 s). Comparar cada candidato con `hmac.compare_digest`
para evitar fugas por timing.

## Secreto y codificación base32

- El secreto se transmite al authenticator en **base32 (RFC 4648)** sin padding,
  porque es lo que esperan las apps y la URI `otpauth://`.
- Tamaño recomendado: ≥ 160 bits (20 bytes) para SHA1, generado con
  `secrets.token_bytes(20)` (CSPRNG). `base64.b32encode` produce el texto base32.
- Para verificar, se decodifica de vuelta a bytes con `base64.b32decode`.

## URI de aprovisionamiento (otpauth://)

Formato del Key URI de Google Authenticator:

```
otpauth://totp/{LABEL}?secret={BASE32}&issuer={ISSUER}&algorithm=SHA1&digits=6&period=30
```

- `LABEL` = `Issuer:cuenta` (p. ej. `Sunalyze Superadmin:admin@x.com`), URL-encoded.
- `issuer` se repite como parámetro para que la app lo muestre y evite colisiones.
- El authenticator del usuario genera el QR a partir de esta URI; **el servidor
  NO genera imagen** (mostramos la URI y el secreto base32 en texto para entrada
  manual). Decisión alineada con el requisito: sin `qrcode`, sin `pyotp`.

## Códigos de recuperación (recovery codes)

Buenas prácticas (NIST 800-63B "look-up secrets", OWASP):

- Generar **N** códigos de un solo uso (aquí N = 10), de entropía alta
  (`secrets.token_hex`), mostrados **una sola vez** al enrolar.
- **Guardar solo el hash**, nunca el código en claro. Como tienen alta entropía
  (no son contraseñas humanas adivinables), un hash rápido tipo SHA-256 con sal
  es aceptable; usamos `hashlib.pbkdf2_hmac` de stdlib para un margen extra y
  formato `pbkdf2$iteraciones$salt$hash`.
- **Consumo único**: al usar uno, se marca/elimina para que no se reutilice.
- Sirven como alternativa al TOTP cuando se pierde el dispositivo.

## Enrolamiento y flujo de login — decisiones de dominio

- **Enrolamiento forzado**: un superadmin sin MFA representa un riesgo para un
  portal de acceso privilegiado y auditado. Decisión: tras password correcto, si
  `mfa_enabled` es falso, **se fuerza al enrolamiento** antes de poder usar el
  resto del portal. Se introduce un estado de sesión intermedio
  (`pending_mfa_user_id`) que concede acceso únicamente a las vistas de
  enrolamiento / verificación, no a las vistas protegidas por
  `require_superadmin`.
- **Verificación al activar**: el secreto se considera "pendiente" hasta que el
  usuario confirma un código TOTP válido; solo entonces se persiste y se marca
  `mfa_enabled = True`. Esto prueba que el authenticator quedó bien configurado.
- **Login con MFA activo**: password correcto → estado `pending_mfa_user_id` →
  pedir código de 6 dígitos (TOTP con ventana ±1) **o** un código de recuperación
  → al validar, sesión completa con `login_user`.
- **Auditoría**: `mfa.enable` al activar, `mfa.login` en login con TOTP correcto,
  `mfa.recovery_used` cuando se consume un código de recuperación.

## Por qué stdlib basta

`hmac`, `hashlib`, `base64`, `struct`, `time` y `secrets` cubren generación de
secreto, cálculo HOTP/TOTP, codificación base32 y hashing de recovery codes. No
hace falta `pyotp` (TOTP) ni `qrcode` (la app del usuario hace el QR).

## Referencias

- RFC 4226 — HOTP: An HMAC-Based One-Time Password Algorithm.
- RFC 6238 — TOTP: Time-Based One-Time Password Algorithm.
- RFC 4648 — Base16, Base32, Base64 Data Encodings.
- Google Authenticator Key URI Format (otpauth://).
- NIST SP 800-63B — Digital Identity Guidelines (look-up secrets, MFA).
- OWASP — Multifactor Authentication / Recovery Codes cheat sheets.

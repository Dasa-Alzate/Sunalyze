# Autenticación multifactor (MFA) del portal de superadmin

## 1. Qué resuelve y por qué le importa al comprador

El portal de superadmin concentra el acceso más sensible de toda la
plataforma: gestión de usuarios, organizaciones y configuración global. Una
contraseña filtrada (phishing, reuso, fuga de un tercero) basta para
comprometer ese acceso si es el único factor.

Sunalyze exige un **segundo factor (TOTP)** a todo superadmin. Aunque un
atacante obtenga la contraseña, no entra sin el código de un solo uso generado
en el dispositivo del administrador legítimo. Para el comprador esto significa:

- Reducción directa del riesgo de toma de control de cuentas privilegiadas, el
  vector con mayor impacto en una brecha.
- Una historia de cumplimiento concreta y demostrable frente a auditores y
  clientes que exigen MFA en accesos administrativos.
- Defensa en profundidad: el factor TOTP se combina con restricción por IP,
  protección CSRF, códigos de recuperación de un solo uso y auditoría de
  eventos. No es una sola barrera, sino varias superpuestas.

## 2. Estándares que satisface

- **RFC 6238 (TOTP)**: contraseñas de un solo uso basadas en tiempo. Es el
  estándar que implementan Google Authenticator, Authy, 1Password y similares.
- **RFC 4226 (HOTP)**: el algoritmo HMAC subyacente sobre el que TOTP define su
  ventana temporal.
- **Prácticas OWASP para MFA**: enrolamiento forzado en accesos privilegiados,
  códigos de recuperación de un solo uso almacenados solo como hash, secretos
  protegidos en reposo y registro auditable de los eventos de autenticación.

La implementación usa exclusivamente la biblioteca estándar de Python para el
cálculo TOTP/HOTP (`hmac`, `hashlib`, `struct`), sin dependencias propietarias,
lo que facilita la revisión y la portabilidad.

## 3. Cómo funciona

**TOTP HMAC-SHA1.** Cada código se deriva de un secreto compartido y del
instante actual mediante HMAC-SHA1, con 6 dígitos y períodos de 30 segundos
(parámetros compatibles con los autenticadores comunes). El QR de enrolamiento
lo genera el propio authenticator a partir de una URI `otpauth://`; el servidor
nunca transmite una imagen.

**Ventana de tolerancia ±1.** La verificación acepta el período actual y los
inmediatamente anterior y posterior, absorbiendo el desfase de reloj entre el
dispositivo y el servidor sin ampliar la ventana de ataque. La comparación usa
`hmac.compare_digest` para no filtrar información por tiempo de respuesta.

**Enrolamiento forzado.** Un superadmin sin MFA es redirigido obligatoriamente
al flujo de alta tras introducir la contraseña; no puede llegar al portal hasta
confirmar un código válido contra el secreto recién generado.

**Códigos de recuperación.** En el alta se entregan diez códigos de un solo
uso, mostrados una única vez. Se almacenan solo como hash PBKDF2-HMAC-SHA256
con sal aleatoria; al consumir uno, se elimina de la lista para impedir su
reutilización.

**Cifrado del secreto en reposo (Fernet).** El secreto TOTP nunca se guarda en
claro en la base de datos. Antes de persistirlo se cifra con **Fernet**
(AES-128 en CBC con autenticación HMAC, de la biblioteca `cryptography`), y se
descifra solo en memoria durante la verificación del código. Una copia de la
base de datos —backup, volcado, acceso de solo lectura— no revela los secretos
sin la clave de cifrado. Si un token resulta corrupto o se cifró con otra clave,
la verificación lo trata como "no enrolado" y fuerza un reenrolamiento en lugar
de fallar.

**Capas adicionales.** El portal puede restringirse por **lista de IP/CIDR**
(opcional, exigida si está configurada) y toda petición que muta estado está
protegida con **CSRF**. Estas capas operan con independencia del segundo factor.

**Auditoría.** Los eventos relevantes se registran como acciones `mfa.*`:
`mfa.enable` (alta), `mfa.login` (segundo factor superado) y
`mfa.recovery_used` (uso de un código de recuperación, con el número de códigos
restantes). Esto deja una traza revisable de quién activó o usó MFA y cuándo.

## 4. Configuración y operación

**`MFA_ENC_KEY`** — clave Fernet que cifra los secretos TOTP en reposo. Debe
ser una clave Fernet válida (base64 urlsafe de 32 bytes). Generación:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Si no se define, la clave se **deriva de forma determinista desde
`SECRET_KEY`**:

```
base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
```

De este modo el cifrado funciona sin configuración adicional, pero se recomienda
una `MFA_ENC_KEY` dedicada en producción para poder rotarla de forma
independiente de la clave de sesión.

**`flask superadmin mfa-reset <email>`** — desactiva el MFA de un superadmin
(por ejemplo, ante pérdida del dispositivo). Limpia secreto, estado y códigos de
recuperación; el usuario deberá reenrolar en su próximo inicio de sesión.

Comandos relacionados: `flask superadmin grant`, `flask superadmin revoke`,
`flask superadmin list`.

## 5. Alcance y límites honestos

- **Solo portal de superadmin (por ahora).** El MFA se exige únicamente en el
  acceso de superadmin. Las cuentas de usuario regulares no tienen este segundo
  factor todavía.
- **Rotación de clave = reenrolamiento.** Cambiar `MFA_ENC_KEY` (o `SECRET_KEY`
  cuando la clave se deriva de ella) invalida los secretos ya cifrados. El
  sistema lo detecta y fuerza el reenrolamiento, pero no hay reencriptado
  automático del parque de secretos.
- **TOTP, no resistente a phishing.** TOTP eleva el listón frente a contraseñas
  robadas, pero no protege contra un proxy de phishing en tiempo real como sí lo
  haría WebAuthn/FIDO2. Es una mejora sustancial, no la barrera definitiva.
- **Sin migración de datos heredados.** El cifrado se introdujo con la propia
  funcionalidad de MFA; no existen secretos en claro previos que reconvertir.

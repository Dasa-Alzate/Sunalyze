# Seguridad de cuentas y auditoria

Esta funcionalidad reune tres capacidades de seguridad que trabajan juntas:
trazabilidad de acciones (bitacora de auditoria), proteccion de cuentas frente a
ataques de fuerza bruta (bloqueo por intentos) e higiene de contrasenas (politica
alineada con estandares modernos). Todo ello disenado para un producto
multi-tenant, donde cada workspace (organizacion) es un compartimento aislado.

## 1. Que resuelve y por que le importa al comprador

Cuando una empresa confia sus proyectos y los datos de su equipo a una plataforma,
necesita responder con confianza a tres preguntas que tarde o temprano le hara su
area de seguridad, su cliente o un auditor:

- **¿Quien hizo que, y cuando?** Cada accion sensible (un inicio de sesion, la
  creacion o el borrado de un proyecto, un cambio de rol de un miembro) deja un
  registro inmutable. Si manana un proyecto desaparece o alguien gana permisos que
  no deberia, la bitacora cuenta exactamente lo que paso, quien fue el actor y
  desde que IP. Esto es trazabilidad y rendicion de cuentas, no una promesa: es un
  dato que se puede consultar.

- **¿Estan protegidas las cuentas frente a quien adivina contrasenas?** Un atacante
  que prueba miles de combinaciones contra una cuenta es uno de los vectores mas
  comunes y baratos. La plataforma bloquea temporalmente la cuenta tras una racha
  de intentos fallidos, cortando el ataque sin necesidad de intervencion humana.

- **¿Se obliga a usar contrasenas decentes?** La mayoria de las brechas no explotan
  un fallo exotico, sino contrasenas debiles o reutilizadas. La politica exige
  longitud suficiente y rechaza las contrasenas mas comunes y filtradas, que son
  precisamente las que un atacante prueba primero.

El valor para el comprador es doble: reduce el riesgo real de incidentes y, ademas,
le da material concreto para sus propios procesos de cumplimiento y para responder
cuestionarios de seguridad de sus clientes.

## 2. Estandares y buenas practicas que satisface

El diseno no se inventa criterios: sigue OWASP ASVS 4.0 (Application Security
Verification Standard), el estandar de referencia para verificar seguridad en
aplicaciones, y los patrones reconocidos de bitacoras de auditoria.

**Anti-automatizacion y bloqueo de cuenta (ASVS 2.2.1).** El estandar pide
controles efectivos contra el testeo de credenciales filtradas y la fuerza bruta, y
fija un techo de no mas de 100 intentos fallidos por hora sobre una sola cuenta. El
bloqueo implementado (5 intentos, ventana y bloqueo de 15 minutos) queda muy por
debajo de ese techo y se apoya en el patron de *soft lockout* recomendado por la
guia de pruebas de OWASP (WSTG), que describe el bloqueo tipico tras 3-5 intentos
con desbloqueo automatico por ventana temporal.

**Politica de contrasenas: longitud sobre composicion (ASVS 2.1.x).** El estandar
moderno prioriza la longitud y desaconseja las reglas de composicion obligatorias
(forzar mayusculas, numeros, simbolos), porque empujan a los usuarios a patrones
predecibles sin ganar seguridad real:

- Longitud minima de 12 caracteres (2.1.1) y maxima de 128 (2.1.2).
- Sin reglas de composicion obligatorias (2.1.9): no se exige mezcla de tipos de
  caracter.
- Rechazo de contrasenas comunes y filtradas (2.1.7), aplicado aqui como una lista
  local de las mas habituales.

**Bitacora de auditoria append-only.** La tabla de auditoria solo admite inserciones:
la aplicacion nunca actualiza ni borra filas existentes. Es el patron estandar de
*audit log* inmutable, que garantiza que el historico no se reescribe desde la
logica de negocio.

## 3. Como funciona (vision tecnica)

### Bitacora de auditoria: `AuditEvent`

El corazon es el modelo `AuditEvent` (`app/models/audit_event.py`), una tabla
append-only y org-scoped. Sus columnas relevantes:

- `actor_user_id` y `actor_email`: quien ejecuto la accion. El correo se
  **desnormaliza** a proposito, para que el evento siga siendo legible aunque mas
  tarde se borre el usuario.
- `org_id`: el eje multi-tenant. Es *nullable* deliberadamente, para admitir
  eventos de plataforma sin organizacion (ver diseno futuro).
- `action`: la accion, con convencion `dominio.verbo` (por ejemplo `auth.login`,
  `project.create`).
- `entity_type` y `entity_id`: a que entidad apunta el evento.
- `payload`: un campo de texto con JSON, donde se guarda el diff o el contexto del
  cambio.
- `ip`: direccion del cliente, resuelta de forma defensiva (respeta
  `X-Forwarded-For` si esta presente).

Hereda de `BaseModel`, por lo que aporta `id`, `created_at` y `updated_at`; la marca
temporal del evento es `created_at`. Hay un indice compuesto por `(org_id, created_at)`
pensado para la lectura habitual: la bitacora de una organizacion ordenada por fecha.

### Atomicidad: el evento viaja con la mutacion

La decision de diseno mas importante esta en `AuditService` (`app/services/audit_service.py`).
El metodo `record(...)` hace `session.add(...)` y `flush()`, pero **no hace commit**.
El commit lo ejecuta el llamador, junto con su propia mutacion, dentro de la **misma
transaccion**.

La consecuencia es la atomicidad: el evento de auditoria y el cambio que describe
son indivisibles. Si la mutacion hace rollback, el evento desaparece con ella; y un
fallo posterior en el request no puede dejar un evento "fantasma" ni perder uno que
ya deberia existir. Esto es mas robusto que registrar la auditoria en un
`after_request` o en un proceso aparte, donde el registro y el cambio pueden
divergir.

El servicio tambien resuelve la IP y el correo del actor de forma defensiva: funciona
aunque se invoque fuera de un contexto de request HTTP (por ejemplo en tests o tareas
en segundo plano), en cuyo caso esos campos quedan a `None` salvo que se pasen
explicitos.

### Que esta cableado hoy

Los puntos donde ya se emiten eventos de auditoria, todos en la misma transaccion que
su mutacion:

- `auth.login` — inicio de sesion correcto, en `AuthService.authenticate`
  (`app/services/auth_service.py`).
- `project.create`, `project.update`, `project.delete` — alta, edicion y borrado de
  proyectos (`app/routes/projects.py`). En la edicion, el payload incluye los campos
  que realmente cambiaron.
- `membership.change_role`, `membership.remove` — cambio de rol y expulsion de un
  miembro (`app/services/membership_service.py`), con el rol previo y el nuevo en el
  payload.

### Bloqueo por intentos fallidos (lockout)

El estado de bloqueo vive en el modelo `User` (`app/models/user.py`), en cuatro
campos: `failed_login_count`, `last_failed_login_at`, `lockout_until` y `last_login_at`.
Se evito crear una tabla de un registro por intento, que creceria sin control; el
comportamiento de ventana se consigue reseteando el contador.

Los parametros estan definidos como constantes del modulo:

- **Umbral:** 5 intentos fallidos (`FAILED_LOGIN_THRESHOLD`).
- **Ventana de conteo:** 15 minutos (`LOGIN_ATTEMPT_WINDOW`). Si el ultimo fallo es
  mas antiguo que la ventana, el contador se reinicia antes de sumar el nuevo. Este
  es el *soft lockout*: mitiga que el propio bloqueo se use como ataque de denegacion
  de servicio contra una cuenta ajena.
- **Duracion del bloqueo:** 15 minutos (`LOCKOUT_DURATION`). Pasado ese tiempo,
  `is_locked_out()` vuelve a permitir el acceso sin intervencion.

El flujo en `AuthService.authenticate`:

1. Si la cuenta esta bloqueada (`is_locked_out()`), se rechaza con un error de
   "cuenta bloqueada temporalmente" antes de comprobar la contrasena.
2. Si las credenciales son incorrectas, se llama a `register_failed_login()` (que
   suma el intento y activa el bloqueo al llegar al umbral) y se persiste en su
   propia transaccion.
3. Si el login es correcto, `register_successful_login()` **resetea** el contador,
   limpia el bloqueo y marca `last_login_at`; en ese mismo commit se escribe el
   evento `auth.login`.

El bloqueo por cuenta no esta solo: el endpoint de login lleva ademas un rate limit
de `10 per minute` por IP. Son defensas en capas: el rate limit frena el volumen por
origen, el lockout protege la cuenta concreta.

### Seguimiento de `last_login`

`last_login_at` se actualiza en cada inicio de sesion correcto
(`register_successful_login`). Da visibilidad del ultimo acceso de cada usuario, util
para detectar cuentas inactivas o accesos inesperados.

### Politica de contrasena

Definida en los esquemas de validacion de autenticacion (`app/schemas/auth.py`,
pydantic v2) y aplicada tanto en el registro como en el restablecimiento de
contrasena. La funcion `_check_password` exige:

- Longitud entre 12 (`PASSWORD_MIN_LENGTH`) y 128 (`PASSWORD_MAX_LENGTH`) caracteres.
- **Sin** reglas de composicion: no se obliga a mezclar mayusculas, numeros ni
  simbolos.
- Rechazo de contrasenas triviales o filtradas, comparando (sin distinguir
  mayusculas) contra una lista local de las mas comunes (`_BREACHED_PASSWORDS`), y
  rechazo de contrasenas con dos o menos caracteres distintos (repeticiones
  triviales).

### Lectura de la bitacora: endpoint protegido

El endpoint `GET /api/audit` (`app/routes/audit.py`) es una capa HTTP fina sobre
`AuditService.list_for_org`. Esta protegido en dos ejes:

- **Permiso `audit:view`** mediante el decorador `@require_permission`
  (`app/authz.py`). En la matriz RBAC, ese permiso lo conceden los roles `owner` y
  `admin`, no `member`. El permiso se evalua contra el rol del usuario en el
  **workspace activo**, no a nivel global: la misma persona puede ser `owner` de su
  espacio y `member` de una empresa.
- **Aislamiento por `org_id`:** la consulta se restringe siempre al
  `current_org_id()` activo, de modo que nadie ve la bitacora de otra organizacion.

Acepta un parametro `limit` (por defecto 100, tope 500) y devuelve los eventos mas
recientes primero.

## 4. Diseno preparado para el futuro

El diseno deja abiertas, a proposito, tres lineas de evolucion sin tener que rehacer
lo construido:

- **Unificacion con `superadmin_audit`.** El portal de superadmin tiene hoy su propia
  bitacora en otra rama. `AuditEvent` es la fundacion general pensada para absorberla:
  `org_id` es nullable (admite eventos de plataforma sin organizacion), `actor_email`
  desnormalizado permite registrar actores que no son `User` de esta tabla, y
  `action`/`entity_type` son strings con un espacio de nombres compartible.

- **Tamper-evidence por hash-chaining.** Hoy la bitacora es append-only, lo que impide
  reescribirla desde la aplicacion. El siguiente nivel es la deteccion de manipulacion:
  encadenar cada entrada al SHA-256 de la anterior (`prev_hash` / `entry_hash`). El
  modelo tiene un esquema de columnas estable que permite anadir esos campos **sin una
  migracion disruptiva**.

- **Lista de contrasenas filtradas via API externa.** La lista local cubre las
  contrasenas mas comunes sin dependencias nuevas. Si se acepta la dependencia externa,
  el siguiente paso natural es consultar Have I Been Pwned (HIBP) con el modelo de
  *k-anonymity* (se envia solo un prefijo del hash, nunca la contrasena), cubriendo
  millones de contrasenas filtradas en lugar de una docena.

## 5. Alcance y limites honestos

Para evitar sobrevender, conviene ser explicito sobre lo que esta y lo que no esta
hoy en el alcance:

- **Cobertura de auditoria parcial.** Estan instrumentadas las acciones listadas
  (login, ciclo de vida de proyectos, cambios de membresia). No toda mutacion del
  sistema emite todavia un evento; la instrumentacion crece por accion a medida que se
  cablea el servicio.
- **Inmutabilidad a nivel de aplicacion, no criptografica.** La bitacora es
  append-only porque la aplicacion no expone update ni delete, pero todavia **no** hay
  tamper-evidence: alguien con acceso directo a la base de datos podria alterar filas
  sin dejar rastro. El hash-chaining (seccion 4) es lo que cerraria esa brecha.
- **La lista de contrasenas filtradas es pequena.** Es un subconjunto local de las mas
  comunes, no la cobertura de un servicio como HIBP. Frena las peores elecciones, no
  todas las filtradas.
- **El lockout es por cuenta.** Mitiga la fuerza bruta dirigida a una cuenta, pero no
  es por si solo una defensa completa contra ataques distribuidos (*credential
  stuffing* desde muchas IP); para eso actuan en capas el rate limit por IP y, en el
  futuro, controles adicionales.
- **`last_login_at` registra el ultimo login correcto**, no un historial de sesiones
  ni la geolocalizacion del acceso.

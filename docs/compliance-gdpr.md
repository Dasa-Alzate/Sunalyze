# Cumplimiento RGPD en Sunalyze

Sunalyze implementa de forma nativa los derechos de datos personales que exige el
Reglamento General de Protección de Datos (RGPD, Reglamento UE 2016/679) y la
normativa española de desarrollo (LOPDGDD, Ley Orgánica 3/2018). Este documento
describe qué cubre la plataforma, por qué importa a quien la compra y cómo funciona
por dentro.

## 1. Qué resuelve y por qué le importa al comprador

Operar un SaaS en la Unión Europea implica tratar datos personales de los usuarios, y
el RGPD obliga al responsable del tratamiento a garantizar derechos concretos del
interesado: acceder a sus datos, llevárselos a otro proveedor y solicitar su supresión.
No es opcional: incumplir expone a sanciones de hasta el 4% de la facturación anual
global o 20 millones de euros, la cifra que sea mayor.

Para un comprador B2B esto se traduce en tres beneficios directos:

- **Reduce su riesgo legal y de sanción.** Al elegir Sunalyze, el cliente hereda una
  plataforma que ya implementa los derechos del interesado, en lugar de tener que
  construirlos o auditar a un proveedor que no los cubre.
- **Acelera su propio cumplimiento.** Los flujos de acceso, portabilidad y supresión
  están disponibles vía API desde el primer día, listos para integrarse en los
  procesos internos de privacidad del cliente.
- **Es un argumento de confianza.** Demostrar cumplimiento RGPD es cada vez más un
  requisito en los procesos de compra y en las due diligence de seguridad. Sunalyze
  llega con esa casilla marcada.

El enfoque de diseño es honesto con el equilibrio entre dos exigencias que el propio
RGPD reconoce: respetar el derecho al olvido del individuo y, a la vez, conservar la
documentación técnico-legal de las instalaciones que la ley obliga a retener.

## 2. Normativa que satisface

Sunalyze cubre los siguientes derechos del interesado del RGPD, en el marco español de
la LOPDGDD:

- **Art. 15 — Derecho de acceso.** El usuario puede obtener una copia de los datos
  personales objeto de tratamiento.
- **Art. 20 — Derecho a la portabilidad.** El usuario puede recibir los datos que ha
  facilitado en un formato estructurado, de uso común y de lectura mecánica (JSON), apto
  para transmitirlos a otro responsable.
- **Art. 17 — Derecho de supresión ("derecho al olvido").** El usuario puede solicitar
  la supresión de sus datos personales. El derecho no es absoluto: el Art. 17.3 exime de
  borrar cuando la conservación es necesaria para cumplir obligaciones legales o para la
  formulación y defensa de reclamaciones, lo que Sunalyze respeta conservando la
  documentación técnica desvinculada de la identidad.

Adicionalmente, la plataforma se apoya en el Considerando 26 del RGPD (los datos
anonimizados de forma irreversible quedan fuera del ámbito del Reglamento) para resolver
la supresión sin destruir la integridad de los datos del proyecto.

Correspondencia entre artículo y endpoint:

| Artículo RGPD | Derecho | Endpoint |
| --- | --- | --- |
| Art. 15 + Art. 20 | Acceso y portabilidad | `GET /api/gdpr/export`, `GET /api/gdpr/export.zip` |
| Art. 17 | Supresión / derecho al olvido | `DELETE /api/gdpr/account` |
| Soporte (base de licitud) | Registro de consentimiento de privacidad | `POST /api/gdpr/consent` |

## 3. Cómo funciona (técnico)

La lógica de dominio vive en `app/services/gdpr_service.py`, aislada del transporte HTTP.
Los endpoints de `app/routes/gdpr.py` son una capa fina que invoca al servicio sobre los
datos del usuario autenticado (`current_user`).

### Exportación de datos (Art. 15/20)

`GdprService.export_data` construye un volcado serializable en JSON con esta estructura:

```
{
  "export_metadata": { "generated_at", "gdpr_articles": ["15","20"], "format_version" },
  "user":            { perfil del usuario, sin password_hash },
  "memberships":     [ { "org_id", "role", "org_nombre" } ],
  "owned_organizations": [
    { "organization": {...}, "projects": [ {...} ] }
  ]
}
```

- El perfil procede de `User.to_dict()`, que **nunca incluye `password_hash`** ni otros
  secretos. El dump elimina además la clave `organizations` redundante del perfil para no
  duplicarla con las membresías.
- Se incluyen todas las membresías del usuario (organización y rol) y, para las
  organizaciones de las que es `owner`, los datos de la organización y sus proyectos.
  Solo se exportan organizaciones donde el usuario es `owner`, por ser el responsable de
  esos datos.
- JSON es el formato idóneo para el Art. 20 por ser estructurado, de uso común y de
  lectura mecánica.

`GdprService.export_zip` reutiliza ese mismo payload y lo empaqueta en un ZIP en memoria
con la librería estándar `zipfile` (compresión `ZIP_DEFLATED`), bajo el nombre
`sunalyze-export-user-<id>.json`.

### Anonimización irreversible (Art. 17)

`User.anonymize` reemplaza la PII directa por valores anónimos que no permiten
reidentificar al usuario:

- **Email** → un token opaco `anon-<hash>@anonymized.invalid`. El `<hash>` se deriva con
  SHA-256 de `<id>:<secreto aleatorio>` (vía `secrets.token_hex`), truncado a 32
  caracteres. El secreto efímero **no se almacena**, por lo que la transformación es
  irreversible (anonimización, no seudonimización). El dominio `.invalid` está reservado
  por la RFC 2606 y nunca resuelve, evitando reenvíos accidentales, y el hash conserva la
  unicidad que exige la constraint `UNIQUE` de `users.email`.
- **Nombre y apellidos** → valores neutros (`'Usuario'`, `'anonimizado'`).
- **`password_hash`** → hash de un secreto aleatorio nuevo, lo que invalida el login.
- **`email_verified`** → `False`.

La operación es **idempotente**: si el email ya termina en `@anonymized.invalid`, la
función retorna sin volver a tocar la PII.

### Soft-delete (borrado lógico)

El `SoftDeleteMixin` (`app/models/database.py`) marca un instante en `deleted_at` en
lugar de eliminar la fila físicamente, preservando la integridad referencial (claves
foráneas) y la documentación retenida:

- `soft_delete()` fija `deleted_at` solo si aún era nulo.
- `is_deleted` es `True` cuando hay marca de borrado.
- `active()` devuelve la query base que **excluye** los registros borrados (filtrado por
  defecto), y `with_deleted()` es el escape para usos administrativos que sí necesitan
  verlos.

### Guard de organización compartida

`GdprService.erase_account` distingue entre organizaciones personales y compartidas para
no romper el acceso de un equipo:

- Si el usuario es el **único miembro** de una organización que posee, esa organización
  se soft-deletea junto con su cuenta.
- Si la organización es **compartida** y el usuario es el **único `owner`**, el borrado se
  **bloquea** con un `Conflict`: debe transferir la propiedad del workspace antes de
  eliminar su cuenta. Así se preserva el acceso del resto del equipo y la integridad del
  workspace.
- Si hay otros `owner`, la cuenta se elimina sin tocar la organización.

Tras evaluar las organizaciones, se eliminan las membresías del usuario, se llama a
`anonymize()` y a `soft_delete()`, y se confirma la transacción.

### Retención legal de proyectos y memoria técnica

Los `projects` y la documentación técnica (memoria técnica de las instalaciones FV) **no
se borran** al ejercer el derecho al olvido. Son documentos técnico-legales que
pertenecen a la organización (`org_id`), no al individuo, y existen obligaciones de
conservación que lo justifican (documentación técnica de instalaciones eléctricas ante
industria y distribuidora, y conservación contable y fiscal de 4 a 6 años según la Ley
General Tributaria y el Código de Comercio). Esto encaja con la excepción del Art. 17.3:
se anonimiza al individuo y se conserva el registro con valor legal desvinculado de su
identidad. Si una organización personal queda sin titular activo, se soft-deletea la
organización pero sus proyectos se conservan.

## 4. Endpoints

Todos operan siempre sobre los datos del usuario autenticado y están protegidos por
control de acceso.

- **`GET /api/gdpr/export`** — Devuelve el dump JSON de datos personales (Art. 15/20).
  Requiere el permiso `ACCOUNT_EXPORT`.
- **`GET /api/gdpr/export.zip`** — Devuelve el mismo export empaquetado como ZIP descargable
  (`Content-Disposition: attachment`, `application/zip`). Requiere `ACCOUNT_EXPORT`.
- **`DELETE /api/gdpr/account`** — Ejerce el derecho al olvido (Art. 17): anonimiza la PII,
  soft-deletea la cuenta y cierra la sesión. Requiere `ACCOUNT_DELETE`.
- **`POST /api/gdpr/consent`** — Registra el consentimiento de la política de privacidad,
  fijando `privacy_accepted_at`. Requiere sesión iniciada (`login_required`).

## 5. Alcance y límites honestos

Esta iteración cubre los derechos centrales del RGPD con un alcance deliberadamente
acotado. Para evitar expectativas equivocadas:

- **Soft-delete acotado a `users` y `organizations`.** Los `projects` no llevan
  soft-delete: se conservan por retención legal y siguen perteneciendo a su organización.
- **Consentimiento como flag mínimo.** `privacy_accepted_at` es un único timestamp de
  aceptación, sin versionado de la política de privacidad ni registro histórico de a qué
  versión consintió el usuario en cada momento.
- **El export cubre datos propios y de organizaciones donde el usuario es `owner`.** No
  incluye datos de organizaciones donde solo es miembro no propietario.

Áreas para endurecer en el futuro: versionado y trazabilidad del consentimiento por
versión de política, ampliación del soft-delete y purgas programadas donde la retención
legal lo permita, y registros de auditoría de los ejercicios de derechos.

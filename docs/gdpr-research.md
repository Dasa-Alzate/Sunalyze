# GDPR / RGPD — investigación de dominio

Notas de dominio para la feature de portabilidad de datos (Art. 15/20) y derecho al
olvido (Art. 17) en Sunalyze (SaaS, España, mercado UE). Marco legal: RGPD
(Reglamento UE 2016/679) + LOPDGDD (Ley Orgánica 3/2018, España).

## Derechos relevantes del interesado

### Art. 15 — Derecho de acceso
El interesado tiene derecho a obtener confirmación de si se tratan datos suyos y, en su
caso, una copia de los datos personales objeto de tratamiento, junto con información
sobre fines, categorías, destinatarios, plazo de conservación y origen.

### Art. 20 — Derecho a la portabilidad
El interesado tiene derecho a recibir los datos personales que le incumben, que haya
facilitado a un responsable, en un **formato estructurado, de uso común y lectura
mecánica** (JSON es idóneo), y a transmitirlos a otro responsable. Aplica cuando el
tratamiento se basa en consentimiento o contrato y se efectúa por medios automatizados.
Diferencia con el Art. 15: la portabilidad cubre solo datos *aportados por el usuario*
(no inferencias/derivados) y exige formato interoperable. En la práctica se satisface un
export JSON que cubre ambos artículos.

### Art. 17 — Derecho de supresión ("derecho al olvido")
El interesado puede obtener la supresión de sus datos personales. **No es absoluto**:
el Art. 17.3 exime de la supresión cuando el tratamiento es necesario para:
- cumplir una **obligación legal** que exija la conservación (17.3.b);
- formular, ejercer o defender **reclamaciones** (17.3.e).

Implicación de diseño: no se puede borrar físicamente todo. La técnica correcta es
**anonimizar** la PII (Considerando 26: los datos anonimizados quedan fuera del ámbito
del RGPD porque ya no permiten identificar a una persona) y conservar los registros con
valor legal/contable desvinculados de la identidad.

## Anonimizar vs. borrar vs. seudonimizar

- **Borrado físico:** elimina la fila. Rompe integridad referencial (FKs), historiales y
  documentos con retención legal. Inviable aquí.
- **Seudonimización (Art. 4.5):** sustituye identificadores por un alias, pero permite
  reidentificar con información adicional (sigue siendo dato personal, sigue bajo RGPD).
- **Anonimización (Cons. 26):** transforma la PII de forma **irreversible** para que no
  pueda asociarse a una persona. Queda fuera del RGPD. Es lo que satisface el Art. 17 sin
  destruir la integridad referencial.

Estrategia adoptada: anonimización irreversible de la PII directa (email, nombre,
apellidos) + soft-delete (marca `deleted_at`) para excluir la cuenta del uso normal sin
perder las FKs ni los documentos que deben retenerse.

### Cómo anonimizamos
- `email` -> token opaco no reversible y no enrutable: `anon-<hash>@anonymized.invalid`.
  El dominio `.invalid` está reservado por RFC 2606 y nunca resuelve, evitando reenvíos
  accidentales. El `<hash>` se deriva con SHA-256 de (id + secreto efímero aleatorio),
  truncado; no se almacena la preimagen, por lo que es irreversible y conserva la unicidad
  exigida por la constraint UNIQUE de `users.email`.
- `first_name` -> `'Usuario'`, `last_name` -> `'anonimizado'` (valores neutros, no PII).
- `password_hash` -> hash de un secreto aleatorio (invalida el login).
- `email_verified` -> `False`.

La anonimización es **idempotente** sobre una cuenta ya anonimizada (no vuelve a tocar
PII si `deleted_at` ya está fijado).

## Retención legal de documentos (España)

La **memoria técnica** y la documentación de las instalaciones FV son documentos
técnico-legales del proyecto, no datos personales del usuario que ejecuta el borrado.
Obligaciones de conservación relevantes que justifican NO borrar el proyecto:
- Conservación de documentación técnica de instalaciones eléctricas/de autoconsumo ante
  industria/distribuidora (vida útil de la instalación, típicamente años).
- Conservación contable y fiscal: facturas y soportes 4 años (Ley General Tributaria) y
  hasta 6 años (Código de Comercio, art. 30).

Por eso los `projects` y la `organization` que los agrupa **no se borran físicamente** al
ejercer el derecho al olvido del usuario: la propiedad de esos datos es de la organización
(el `org_id`), no del individuo. Se anonimiza al individuo y, si una organización personal
queda sin titular activo, se soft-deletea la organización pero se conservan sus proyectos.

## Decisiones de alcance (qué entra en esta feature)

- **Soft-delete (`deleted_at`)** se aplica a `users` y `organizations`. Son las entidades
  que el flujo de erasure marca. Los `projects` se conservan por retención legal y siguen
  perteneciendo a su org; no se les añade soft-delete en esta iteración.
- **Filtrado por defecto:** las consultas de cuentas/orgs excluyen los registros con
  `deleted_at` no nulo. Se ofrece un escape (`with_deleted`) para usos administrativos.
- **Export (Art. 15/20):** cubre los datos del propio usuario (perfil, membresías) y de
  las organizaciones de las que es `owner` (datos de la org + sus proyectos), en JSON,
  con opción de descarga en ZIP (stdlib `zipfile`).
- **Consentimiento (flag mínimo):** `User.privacy_accepted_at` (timestamp nullable). Marca
  simple de aceptación de la política de privacidad; sin flujo de versionado en esta
  iteración.

## Qué exporta el dump (Art. 15/20)

```
{
  "export_metadata": { generated_at, gdpr_articles, format_version },
  "user": { perfil sin password_hash },
  "memberships": [ { org_id, role, org_nombre } ],
  "owned_organizations": [
    { organization {...}, projects: [ {...} ] }
  ]
}
```

Solo se incluyen organizaciones donde el usuario es `owner` (es el responsable de esos
datos). No se exporta `password_hash` ni secretos.

## Referencias

- RGPD (UE) 2016/679: arts. 4.5, 15, 17, 20; considerando 26.
- LOPDGDD (Ley Orgánica 3/2018), España.
- RFC 2606 (dominios reservados, `.invalid`).
- Ley General Tributaria (conservación 4 años) y Código de Comercio art. 30 (6 años).

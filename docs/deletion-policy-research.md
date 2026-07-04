# Política de borrado — investigación y decisiones

## Contexto

Hoy conviven tres capas descoordinadas:

- **Soft-delete** (`SoftDeleteMixin.deleted_at`) en las raíces de tenant y catálogo:
  `Organization`, `User`, `Project`, `Catalog`.
- **Cascadas ORM** `cascade='all, delete-orphan'` declaradas en varios `relationship`,
  pero **inertes a nivel BD**: las FK no llevan `ondelete`, así que un borrado emitido
  por la BD (o un hard-delete real) no propaga y viola la integridad referencial.
- **FKs a `users`** sin `ondelete`: al intentar borrar un actor, la BD aborta.

El derecho al olvido (`GdprService.erase_account`) es **anonimizar-en-sitio** (Art. 17):
anonimiza la PII del usuario y hace soft-delete; no hard-deletea. Esa política **no cambia**.

Este trabajo alinea BD + ORM para que el hard-delete sea **seguro y coherente**, sin tocar
los flujos de usuario (soft-delete, `erase_account`).

## Política canónica

1. **Raíces de tenant/catálogo** (`Organization`, `User`, `Project`, `Catalog`): soft-delete.
   El borrado normal marca `deleted_at`; nunca se hard-deletea desde la app.
2. **Referencia a actor/autor** (quién hizo algo, el registro debe sobrevivir sin actor):
   `ondelete='SET NULL'` + columna `nullable=True`. Nada de delete-orphan en el ORM.
3. **Hijo de propiedad (composición)** (muere con su padre): `ondelete='CASCADE'`, alineado
   con el `cascade='all, delete-orphan'` del ORM + `passive_deletes=True` para delegar en la BD.
4. **Lookup/catálogo** (referencia a un elemento elegido; borrar el padre no debe romper el
   hijo silenciosamente): `RESTRICT`/sin cambio (default de la BD aborta el borrado del padre
   mientras esté referenciado).

## Clasificación por FK

### SET NULL — referencia a actor/autor (el registro sobrevive)

| Tabla.columna | Referencia | Justificación |
|---|---|---|
| `audit_events.actor_user_id` | users | Log append-only; `actor_email` desnormalizado sobrevive al borrado del actor. |
| `audit_events.org_id` | organizations | Bitácora de cumplimiento: debe sobrevivir al borrado de la org (ya nullable para eventos de plataforma). |
| `notifications.actor_user_id` | users | Quién originó la notificación; la notificación sigue siendo válida sin él. |
| `invitations.invited_by_user_id` | users | Quién invitó; la invitación pertenece a la org, no al invitador (columna pasa a nullable). |
| `invitations.accepted_user_id` | users | Quién aceptó; dato histórico opcional. |
| `memoria_signatures.signed_by_user_id` | users | Firmante; la firma es prueba de integridad del PDF y debe sobrevivir (columna pasa a nullable). |
| `project_events.actor_user_id` | users | Actor de la transición de estado; el evento es inmutable y debe sobrevivir. |
| `financial_scenarios.created_by` | users | Autor del escenario; el escenario pertenece al proyecto. |
| `report_templates.created_by` | users | Autor de la plantilla; la plantilla pertenece a la org. |
| `generated_documents.generated_by` | users | Quién generó el PDF; el documento es artefacto de la org/proyecto. |
| `flag_overrides.created_by` | users | Quién concedió el override; el override sigue vigente por su ámbito. |
| `superadmin_audit.actor_user_id` | users | Actor de acción de plataforma; `actor_email` desnormalizado sobrevive. |
| `support_tickets.requester_user_id` | users | Solicitante; `requester_email` desnormalizado sobrevive. |
| `support_tickets.org_id` | organizations | Ticket de soporte de plataforma; sobrevive al borrado de la org. |
| `template_installations.category_id` | template_categories | La entrada de biblioteca sobrevive sin categoría. |

### CASCADE — hijo de propiedad / composición (muere con su padre)

| Tabla.columna | Padre | Justificación |
|---|---|---|
| `memberships.user_id` | users | Pertenencia; `User.memberships` es delete-orphan. |
| `memberships.org_id` | organizations | Pertenencia; `Organization.memberships` es delete-orphan. |
| `org_branding_profiles.org_id` | organizations | Marca 1:1 de la org. |
| `catalogs.org_id` | organizations | Catálogo privado del workspace (marketplace tiene org_id NULL, intacto). |
| `catalog_subscriptions.org_id` | organizations | Suscripción del workspace. |
| `catalog_subscriptions.catalog_id` | catalogs | Suscripción sin sentido sin su catálogo. |
| `projects.org_id` | organizations | El proyecto pertenece a la org. |
| `installations.project_id` | projects | Instalación 1:1 nacida del proyecto. |
| `installations.org_id` | organizations | Instalación del workspace. |
| `maintenance_visits.installation_id` | installations | `Installation.maintenance_visits` delete-orphan. |
| `maintenance_visits.org_id` | organizations | Del workspace. |
| `installation_incidents.installation_id` | installations | `Installation.incidents` delete-orphan. |
| `installation_incidents.org_id` | organizations | Del workspace. |
| `production_readings.installation_id` | installations | `Installation.readings` delete-orphan. |
| `production_readings.org_id` | organizations | Del workspace. |
| `memoria_signatures.project_id` | projects | `Project.signatures` delete-orphan. |
| `memoria_signatures.org_id` | organizations | Del workspace. |
| `project_events.project_id` | projects | `Project.events` delete-orphan. |
| `project_events.org_id` | organizations | Del workspace. |
| `financial_scenarios.project_id` | projects | Escenario del proyecto. |
| `financial_scenarios.org_id` | organizations | Del workspace. |
| `notifications.recipient_user_id` | users | Proyección por-destinatario; sin destinatario no existe. |
| `notifications.org_id` | organizations | Del workspace. |
| `invitations.org_id` | organizations | Invitación del workspace. |
| `support_ticket_messages.ticket_id` | support_tickets | `SupportTicket.messages` delete-orphan. |
| `flag_overrides.flag_key` | flags | Override sin sentido sin su flag. |
| `report_templates.org_id` | organizations | Plantilla del workspace (system tiene org_id NULL, intacto). |
| `template_versions.template_id` | report_templates | `ReportTemplate.versions` delete-orphan. |
| `template_categories.org_id` | organizations | Del workspace. |
| `template_labels.org_id` | organizations | Del workspace. |
| `template_installations.org_id` | organizations | Del workspace. |
| `template_installations.template_id` | report_templates | La entrada de biblioteca apunta a una plantilla concreta. |
| `installation_labels.installation_id` | template_installations | Puente n:n. |
| `installation_labels.label_id` | template_labels | Puente n:n. |
| `generated_documents.org_id` | organizations | Del workspace. |
| `generated_documents.project_id` | projects | Documento del proyecto. |
| `generated_documents.template_id` | report_templates | Documento generado desde la plantilla. |
| `generated_documents.template_version_id` | template_versions | Versión fijada usada. |

### RESTRICT / sin cambio — lookup/catálogo (borrar el padre no debe romper el hijo)

| Tabla.columna | Referencia | Justificación |
|---|---|---|
| `projects.panel_id` | panels | Equipo elegido; referencia de catálogo, no composición. |
| `projects.inverter_id` | inverters | Íd. |
| `projects.battery_id` | batteries | Íd. |
| `panels.catalog_id` | catalogs | Fuera del alcance de audit; catálogo con soft-delete, el default RESTRICT protege. |
| `inverters.catalog_id` | catalogs | Íd. |
| `wires.catalog_id` | catalogs | Íd. |
| `batteries.catalog_id` | catalogs | Íd. |

## Decisiones discutibles (para revisión)

- **`audit_events.org_id` y `support_tickets.org_id` → SET NULL** en vez de CASCADE:
  al ser registros de cumplimiento/soporte append-only, se preservan tras el borrado de la
  org (ambas columnas ya eran nullable). Discutible si se prefiere no retener nada de una
  org borrada.
- **`generated_documents.template_id` / `template_version_id` → CASCADE**: borrar una
  plantilla borra su histórico de PDFs generados. Alternativa sería RESTRICT (no permitir
  borrar plantillas usadas). Se eligió CASCADE por coherencia con el borrado en cascada de
  la org y porque las columnas son NOT NULL (SET NULL exigiría cambiarlas). SQLite admite
  múltiples caminos de cascada sin error.
- **`memoria_signatures.signed_by_user_id` e `invitations.invited_by_user_id` pasan de
  NOT NULL a NULL** para admitir SET NULL, según la política de "el registro sobrevive al
  actor". En la práctica el usuario nunca se hard-deletea (GDPR anonimiza en sitio), así que
  el SET NULL solo se dispara ante un hard-delete manual.

## Notas de implementación

- Migración única batch-safe (`op.batch_alter_table`, recrea la tabla en SQLite). Se pasa la
  `naming_convention` del proyecto a `batch_alter_table` para que Alembic reconozca por nombre
  las FK reflejadas (SQLite no persiste nombres de constraint) y pueda soltarlas/recrearlas.
- `down_revision = 'b2c3d4e5f6a7'` (head actual). Un único head.
- ORM: se añade `passive_deletes=True` a las relaciones delete-orphan cuyas FK pasan a CASCADE
  (Organization/User.memberships, Project.signatures/events, Installation.maintenance_visits/
  incidents/readings, SupportTicket.messages, ReportTemplate.versions) para delegar en la BD.
- Tests con SQLite requieren `PRAGMA foreign_keys=ON` por conexión para ejercitar las FK
  (SQLite las ignora por defecto).

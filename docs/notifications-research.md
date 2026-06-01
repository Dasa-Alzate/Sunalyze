# Notificaciones (bandeja) + trabajo pendiente (derivado) — research/analisis

## Regla de oro (pending-work.md §2)
- Las **notificaciones se almacenan** (eventos puntuales dirigidos a un usuario).
- El **trabajo pendiente se deriva** del estado actual al vuelo — NO se persiste como filas.
- El **badge** usa la misma fuente que la vista (no hay contador aparte).

## Patrones del repo reaprovechados
- `BaseModel` (id/created_at/updated_at), multi-tenant por `org_id`.
- Auditoria ya existe: `AuditService.record(...)` hace `add`+`flush` (NO commit); el
  llamador hace el commit de su mutacion. Las notificaciones siguen el mismo contrato:
  `NotificationService.notify(...)` hace `add`+`flush`, el service de dominio commitea.
  Asi notificacion y cambio son atomicos (rollback del cambio => rollback notificacion).
- Rutas finas en `routes/`, dominio en `services/` (sin Flask), IDOR -> `NotFound` (404).
- Sesion: `current_user()` + `current_org_id()` desde `app.security`.
- Migraciones batch-safe con `server_default`, naming_convention via metadata, down_revision
  reencadenado al head actual `827266176ee7`.

## Modelo Notification
Tabla `notifications` (BaseModel, org-scoped):
- `recipient_user_id` FK users (index) — el dueno de la notificacion.
- `org_id` FK organizations (index) — workspace donde ocurrio.
- `type` String — `dominio.verbo` (p.ej. `invitation.received`, `membership.role_changed`).
- `actor_user_id` FK users nullable — quien la origino.
- `entity_type` / `entity_id` — a que objeto apunta.
- `payload` JSON (Text serializado) — contexto para render.
- `read_at` DateTime nullable (index) — leida o no.
- `to_dict()` resuelve `link` desde `entity_type` -> ruta SPA.

Fan-out **on write**: una fila por destinatario. Cada usuario lee SOLO las suyas
(`recipient_user_id == current_user`), scoped tambien por `org_id` activo.

## NotificationService
`notify(recipients, type, actor=None, org_id=None, entity_type=None, entity_id=None, payload=None)`
- `recipients`: iterable de user_id o User; se normaliza a ids unicos.
- Regla: **nunca notificar al propio actor** (se filtra `actor.id`).
- Dedupe basico: ids unicos por fan-out.
- `add`+`flush` (sin commit) -> el caller commitea junto a su cambio.
- Helpers de lectura: `list_for(user_id, org_id, page, per_page)`, `unread_count(...)`,
  `mark_read(user_id, org_id, notification_id)` (IDOR->NotFound), `mark_all_read(...)`.

### Disparadores cableados (en services existentes)
- `MembershipService.invite`: si el email ya es un usuario registrado -> `invitation.received`
  a ese usuario (no al inviter).
- `MembershipService.change_role`: -> `membership.role_changed` al target (no al actor).
- `MembershipService.remove`: -> `membership.removed` al expulsado (no al actor). Se emite
  ANTES del delete del membership (el destinatario es el user, que sigue existiendo).
- `LegalizationService.sign_memoria` (= "memoria generada/firmada"): -> `memoria.signed`
  a los demas miembros de la org (no al firmante).

`generar_pdf` (route `/imprimir/memoria-pdf`) es anonimo y sin org: no es punto de
disparo. El punto org-scoped con actor y entidad es la firma de memoria.

## PendingWorkService (DERIVADO)
Registro de checks `(fn) -> {type,label,count,link}` que consultan el estado vigente.
Fuentes iniciales:
- `projects.draft`: proyectos en estado `borrador` en la org.
- `analysis.stale`: proyectos sin `resultados` (analisis no ejecutado/desactualizado).
- `invitations.pending`: invitaciones `pending` no expiradas de la org.
- `account.email_unverified`: el usuario activo con `email_verified == False`.
- `memoria.missing`: proyectos en `borrador`/`en_revision` sin firma de memoria vigente.

Endpoint `GET /api/pending-work` ejecuta los checks al vuelo y devuelve los que `count>0`.
Sin tablas: un proyecto en borrador aparece; al cambiar de estado, desaparece.

## Endpoints
- `GET /api/notifications` (paginado: page/per_page; scoped user+org).
- `GET /api/notifications/unread-count`.
- `POST /api/notifications/<id>/read` (IDOR->404).
- `POST /api/notifications/read-all`.
- `GET /api/pending-work`.

## Para el frontend
- Provider/poll: `unread-count` (ligero) en intervalo; al abrir el centro, `GET /notifications`.
- Campana + badge: badge = `unread-count` (misma fuente que la lista, no inventado).
- Centro de notificaciones: lista paginada con `link` resuelto; marcar leida / marcar todas.
- Panel "trabajo pendiente": render directo de `GET /pending-work` (items derivados).

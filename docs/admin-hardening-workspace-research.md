# Admin hardening + workspace switching — investigación y decisiones

Cubre dos hallazgos de auditoría entregados en la rama `feat/admin-hardening-workspace`.

## Hallazgo #20 — defensa en profundidad en `/api/admin/*`

### Estado previo
- El portal superadmin (`app/superadmin/`) filtra por IP en `before_request` del blueprint
  (`enforce_ip` en `app/superadmin/guards.py`), usando `SUPERADMIN_IP_ALLOWLIST`
  (CSV/;-separado de IPs o CIDR) y `SUPERADMIN_TRUST_PROXY` (primer salto de
  `X-Forwarded-For`). Allowlist vacía = sin filtro.
- La API `/api/admin/*` (`app/routes/admin.py`: flags, organizations, users) vive en el
  dominio principal y solo exige `require_superadmin`: un superadmin comprometido puede
  operarla desde cualquier IP.

### Decisión
- La lógica de allowlist se extrae a un módulo neutro `app/ip_allowlist.py`
  (`client_ip`, `ip_allowed`), sin dependencias de superadmin ni de modelos. Es capa
  HTTP pura, análoga a `app/security_headers.py`.
- `app/superadmin/guards.py` reexporta/consume esas funciones; su `enforce_ip` sigue
  devolviendo la página HTML `denied.html` (portal server-rendered).
- `admin_bp` gana un `before_request` que, con allowlist configurada e IP fuera de la
  lista, lanza `Forbidden` (`DomainError`, 403 JSON, code `admin.ip_not_allowed`): la API
  responde con el contrato JSON del resto de la aplicación, nunca HTML.
- Allowlist vacía → sin filtro, idéntico al comportamiento actual (no rompe desarrollo).

## Hallazgo #25 — código muerto + cambio de workspace

### Estado previo
- `require_membership` (`app/security.py`) no tiene ningún llamador (verificado con grep
  sobre todo el repo): código muerto, se elimina.
- El workspace activo es `session['org_id']` (fuente única: `current_org_id()` /
  `set_current_org()` en `app/security.py`). Solo cambia en `login_user` y al aceptar una
  invitación (`/api/invitations/<token>/accept`): un usuario multi-org no puede volver a
  un workspace anterior sin recibir otra invitación.

### Decisión
- Dominio en `MembershipService` (`app/services/membership_service.py`):
  `workspaces(user, active_org_id)` lista las membresías con org viva y marca la activa;
  `switch_workspace(user, org_id)` valida la Membership y audita `workspace.switch` vía
  `AuditService` (mismo patrón que `membership.change_role`).
- Membership inexistente u org borrada → `NotFound` 404 `workspace.not_found`,
  consistente con el patrón IDOR→404 del repo (p. ej. `GET /api/projects/<id>` de otra
  org devuelve 404, no 403, para no revelar existencia).
- Rutas finas en `app/routes/workspace.py` (`workspace_bp`): `GET /api/workspace` y
  `POST /api/workspace/switch` (body validado con `SwitchWorkspaceSchema`, pydantic v2,
  en `app/schemas/members.py`). El endpoint de switch actualiza la sesión con
  `set_current_org(...)` — la misma fuente que resuelve `current_org_id()`.
- Frontend ligero: `WorkspaceSwitcher` (`frontend/src/app/WorkspaceSwitcher.jsx`) en el
  pie del sidebar, junto al chip de usuario. Solo se renderiza con >1 workspace; usa el
  `sun-select` existente. Al cambiar llama a `POST /api/workspace/switch` y recarga la
  página (invalidación total del estado, sin rediseño). El callback `onSwitched` es
  inyectable para tests.

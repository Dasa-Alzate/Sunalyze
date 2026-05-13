# Portal de superadmin

Portal interno servido **junto a la plataforma principal**, en su propio subdominio
(`admin.tudominio`) o, en desarrollo, bajo `/superadmin`. Renderizado en servidor
(Jinja), aislado de la SPA de clientes. Toda acción con efecto queda auditada.

## Capas de protección (de fuera hacia dentro)

1. **Restricción por IP** (`SUPERADMIN_IP_ALLOWLIST`): `before_request` del blueprint.
   Filtra ANTES del login — fuera de la allowlist ni se ve el formulario (403).
   Vacía → no bloquea (dev); definida → se exige. Acepta IPs y CIDRs.
2. **Sesión + rol** (`is_superadmin`): `require_superadmin` en cada vista. Sin sesión
   → redirige al login; autenticado sin rol → 403.
3. **CSRF** (Flask-WTF) en todos los formularios POST.
4. **Rate limit** en el login (10/min).
5. **Auditoría** (`superadmin_audit`): actor, IP, acción, objetivo y detalle.

El alta del **primer** superadmin no se puede hacer desde la web (huevo-gallina):

```
flask superadmin grant  <email>
flask superadmin revoke <email>
flask superadmin list
```

## Secciones

- **Dashboard**: métricas (usuarios, orgs por plan, proyectos, equipos, equipos por
  revisar, tickets abiertos/pendientes).
- **Equipos por revisar**: paneles/inversores con `needs_review=True` (alimentado por
  los scrapers); acción de aprobar (limpia el flag).
- **Migraciones**: revisión actual vs head, historial Alembic, y aplicar `upgrade`
  con doble confirmación + auditoría. El `downgrade` NO se expone por la web.
- **Usuarios**: listado; conceder/revocar superadmin (no sobre uno mismo).
- **Organizaciones**: listado con tipo, plan, asientos y nº de miembros.
- **Tickets de soporte**: bandeja con filtro por estado, detalle con conversación,
  responder (mensaje de staff) y cambiar estado.
- **Auditoría**: últimas 200 acciones.

## Despliegue como subdominio

Define `SERVER_NAME` (p. ej. `sunalyze.app`) y `SUPERADMIN_SUBDOMAIN=admin`; el portal
queda en `admin.sunalyze.app`. Apunta el DNS y haz que el proxy reenvíe ese host a la
app. Para compartir la cookie de sesión entre dominios usa `SESSION_COOKIE_DOMAIN`.
Sin `SERVER_NAME`, el portal se monta en `/superadmin` (desarrollo).

Detrás de proxy, activa `SUPERADMIN_TRUST_PROXY=1` para que el filtro de IP lea
`X-Forwarded-For` (de lo contrario filtra por la IP del proxy).

## Nota de ramas

Las columnas `needs_review`/`review_notes` en `panels`/`inverters` aparecen también en
la rama `products-scrapper`. Al integrar, una migración prevalece; reconciliar al merge.

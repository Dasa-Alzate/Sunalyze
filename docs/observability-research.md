# Observabilidad: investigación

Fundación mínima para producción: endpoint de salud consumible por orquestadores y captura
opcional de errores con Sentry. Rama `feat/observability` sobre `main` (`fbb565d`).

## Endpoint de salud

- Patrón estándar (Kubernetes probes, Docker healthchecks, load balancers): `GET /health`
  sin autenticación, respuesta JSON pequeña, HTTP 200 = sano, HTTP 503 = degradado.
- Chequeos incluidos y su semántica:
  - `db`: `SELECT 1` vía `db.session`. Es la dependencia dura — si falla, la app no puede
    servir nada útil → 503 con `status: "degraded"`.
  - `cache`: roundtrip `set`/`get` de una clave efímera con TTL corto. Con `SimpleCache`
    (default local) nunca falla; con Redis caído la app sigue funcionando (la caché es
    optimización, no dependencia dura) → se refleja `"error"` en el campo pero NO baja a 503,
    para no provocar reinicios en cascada por una dependencia blanda.
- No filtrar información: nada de versiones, hostnames, stack traces ni mensajes de
  excepción. Solo `ok`/`error` por componente. Los detalles van a los logs, no al probe.
- Rate limiting: los probes pegan cada 20–30 s desde la misma IP. Flask-Limiter 4.1.1
  expone `@limiter.exempt` (decorador de vista) que registra el nombre cualificado en
  `limit_manager.add_route_exemption` con scope `APPLICATION|DEFAULT|META`; cubre límites
  default y application-wide presentes o futuros. Verificado en el código fuente de la
  versión instalada.
- Enrutado: el catch-all de la SPA usa `@app.route('/<path:path>')`. En el mapa de URLs de
  Werkzeug las reglas estáticas (`/health`) puntúan por delante de las reglas con
  convertidores `path`, así que el blueprint captura `/health` siempre. Se verifica con test.
- Docker Compose healthcheck del servicio `web`: `curl -fsS` ya disponible en la imagen
  runtime (instalado en el Dockerfile). `start_period: 120s` porque el entrypoint espera a
  la BD y ejecuta `flask db upgrade` antes de arrancar gunicorn; en el primer deploy la
  migración completa tarda.

## Sentry opcional

- SDK: `sentry-sdk[flask]` (extra `flask` arrastra `blinker`, ya presente). Puro Python,
  sin dependencias de sistema. Última versión estable en PyPI: 2.64.0.
- Activación exclusivamente por entorno, patrón del repo para deps opcionales (boto3/rq):
  import perezoso dentro del `if dsn:` — sin DSN no se importa el módulo y la app arranca
  aunque el paquete no esté instalado.
- Config:
  - `SENTRY_DSN` (default `None`) — vacío/ausente = desactivado.
  - `SENTRY_ENVIRONMENT` — default `production` si `FLASK_ENV=production`, si no
    `development`.
  - `SENTRY_TRACES_SAMPLE_RATE` (float, default `0.0`) — tracing apagado por defecto;
    subirlo tiene coste de cuota.
- `send_default_pii=False`: RGPD — sin IPs de usuario, cookies ni datos de request con PII
  en los eventos. Es además el default del SDK, se fija explícito como declaración de
  postura.
- `FlaskIntegration` captura excepciones no manejadas vía señales de Flask; no requiere
  middleware manual.

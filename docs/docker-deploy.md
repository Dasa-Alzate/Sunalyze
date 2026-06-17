# Despliegue con Docker

## ¿Corre en un Ubuntu Server sin tocar el código?

**Sí, el código es portable** (no hay rutas absolutas ni dependencias del SO), pero
"clonar y arrancar" no basta: hace falta provisión. Sin Docker, en un Ubuntu limpio
necesitarías:

1. **Librerías de sistema:**
   - WeasyPrint (genera los PDF de la memoria) requiere Pango/HarfBuzz/fuentes:
     `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core` (+ jpeg/openjpeg).
   - `mysqlclient` se compila: `build-essential pkg-config python3-dev default-libmysqlclient-dev`.
2. **Node 18+** para compilar el SPA (`frontend/dist` está en `.gitignore`, no se versiona).
3. **Servidor WSGI:** `run.py` usa el servidor de desarrollo de Flask (`debug=True`),
   que NO es para producción. `gunicorn` ya está en `requirements.txt`; se arranca con
   `gunicorn -c docker/gunicorn.conf.py wsgi:app`.
4. **`.env`** con `SECRET_KEY` y `DATABASE_URL` (y `FLASK_ENV=production`).
5. **MySQL** accesible y migraciones aplicadas (`flask db upgrade`).
6. **Reverse proxy** (nginx/Caddy) por delante para TLS.

Docker empaqueta los puntos 1–5 de forma reproducible. **El único añadido de código**
es `wsgi.py` (envuelve la app con `ProxyFix` para leer la IP real tras el proxy); no
es lógica de negocio, es pegamento de despliegue, y el resto del refactor queda intacto.

## Arquitectura de la imagen

`Dockerfile` multi-etapa:
1. **frontend** (`node:20-slim`): `npm ci` + `npm run build` → `frontend/dist`.
2. **builder** (`python:3.12-slim`): instala toolchain + `default-libmysqlclient-dev`,
   crea un venv en `/opt/venv` con todas las dependencias.
3. **runtime** (`python:3.12-slim`): solo librerías de ejecución (Pango, fuentes,
   `libmariadb3`), copia el venv y el `dist`, corre como usuario no-root, arranca gunicorn.

`docker/entrypoint.sh` espera a la base de datos, aplica `flask db upgrade` y luego
ejecuta gunicorn.

## Arranque

```bash
cp .env.docker.example .env.docker      # rellena SECRET_KEY y contraseñas
docker compose --env-file .env.docker up -d --build
# la app queda en http://<host>:8000  (sirve el SPA + la API)
```

`docker compose` levanta `db` (MySQL 8.4, con healthcheck y volumen persistente) y
`web`. `web` espera a que `db` esté `healthy`, migra y arranca.

## Producción

- Pon un **reverse proxy con TLS** (nginx/Caddy/Traefik) delante de `web:8000`.
  El portal de superadmin (rama `superadmin-portal`) va en un subdominio: enruta
  `admin.tudominio` al mismo contenedor con `SERVER_NAME` + `SUPERADMIN_SUBDOMAIN`.
- `SUPERADMIN_TRUST_PROXY=1` ya viene por defecto en compose para que el filtro de IP
  y el rate-limit lean `X-Forwarded-For` (gracias a `ProxyFix` en `wsgi.py`).

## Limitaciones conocidas (deuda, no bloqueante)

- **Rate-limit y cache son por proceso** (`memory://` / `SimpleCache`). Con varios
  workers de gunicorn los límites no se comparten. `redis` ya está en `requirements`;
  el siguiente paso es hacer `RATELIMIT_STORAGE_URI`/`CACHE_TYPE` configurables por env
  y añadir un servicio `redis` al compose. Mientras tanto, `WEB_CONCURRENCY=1` da
  límites exactos.
- La imagen no fija versión de fuentes; si la memoria PDF necesita una tipografía
  concreta, añádela en la etapa runtime.

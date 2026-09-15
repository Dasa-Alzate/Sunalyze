---
name: levantar-sunalyze
description: Use when starting, running, deploying or smoke-testing the Sunalyze app locally - the full Docker Compose stack (MySQL 8.4 + Redis + gunicorn) or the native dev server. Covers the env vars the compose demands, reusing the existing database volume, and the failure modes that actually happen (Alembic multiple heads, AirPlay on port 5000, missing MFA_ENC_KEY).
---

# Levantar Sunalyze

Dos caminos. El de Docker es el que se parece a producción y el que hay que usar para
verificar que algo "funciona de verdad"; el nativo es para iterar en el código.

## Camino 1 — Stack completo con Docker (fiel a producción)

**Requisitos:** Docker Desktop arrancado (`docker info` responde) y `.env.docker` en la
raíz. Si no existe: `cp .env.docker.example .env.docker` y rellena los secretos.

`.env.docker` debe tener las 5 claves obligatorias, o el compose aborta antes de
construir nada (usa la sintaxis `${VAR:?mensaje}`, fail-fast deliberado):

| Clave | Cómo generarla |
|---|---|
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `MFA_ENC_KEY` | `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `REDIS_PASSWORD` | `python3 -c "import secrets; print(secrets.token_hex(16))"` |
| `MYSQL_PASSWORD` | idem |
| `MYSQL_ROOT_PASSWORD` | idem |

```bash
docker compose -p sunalyze --env-file .env.docker up -d --build --wait
```

**`-p sunalyze` no es opcional si quieres tus datos.** Compose nombra los volúmenes con
el nombre del proyecto, que por defecto es el del directorio. El volumen con los datos
reales es `sunalyze_db_data`; desde un worktree o una carpeta con otro nombre, sin `-p`
te crea una base de datos vacía y parecerá que perdiste todo.

El primer build tarda varios minutos: compila el SPA con Vite, instala las
dependencias de Python y compila `mysqlclient`. El entrypoint espera a MySQL, aplica
las migraciones y arranca gunicorn.

### Verificación (no te fíes de "Started", condúcelo)

```bash
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{}'
```

Esperado:

- `/health` → `{"cache":"ok","db":"ok","status":"ok"}`. Si `cache` falla, es la
  `REDIS_PASSWORD`; si falla `db`, mira los logs de migraciones.
- `/` → 200 con el HTML del SPA (`<title>Sunalyze</title>`).
- login sin CSRF → `{"error":"Token CSRF inválido o ausente..."}`. **Esto es un acierto,
  no un fallo**: demuestra que el CSRF de producción está activo.

Para entrar por la web hace falta una cuenta. El contenedor corre con
`FLASK_ENV=production`, así que el seed se niega (`Aborted!`) salvo que lo fuerces:

```bash
docker compose -p sunalyze --env-file .env.docker exec -e ALLOW_SEED_DEMO=1 web flask seed demo
```

Credenciales en el README. **Es idempotente pero añade una organización y tres
proyectos de demo**: no lo lances contra una base de datos con trabajo real dentro.

Apagar: `docker compose -p sunalyze down` — **sin `-v`**, que borra los datos.

## Camino 2 — Nativo (recarga en caliente)

```bash
export FLASK_APP=run DATABASE_URL="sqlite:///$PWD/dev.db" SECRET_KEY=dev
flask db upgrade && flask run -p 5001
cd frontend && FLASK_URL=http://127.0.0.1:5001 npm run dev
```

Abre `http://localhost:5173`.

**En macOS usa siempre `-p 5001`.** El puerto 5000 lo ocupa el receptor de AirPlay
(aparece como `ControlCenter` en `lsof -nP -iTCP:5000`) y responde 403 en vez de
rechazar la conexión, así que el síntoma parece un fallo de la app.

## Fallos que ocurren de verdad

**El contenedor `web` arranca y muere sin servir.** Mira el log del entrypoint:

```bash
docker logs sunalyze-web-1 2>&1 | grep -E "entrypoint|Running upgrade|Listening|Error"
```

Si ves `Multiple head revisions are present for given argument 'head'`, el grafo de
Alembic tiene dos puntas — pasa cuando una rama de vida larga se mergea y su migración
sigue colgando del head de cuando se creó. `flask db upgrade` resuelve `head` en
singular y aborta; con `set -e` en el entrypoint, el contenedor muere antes de
`exec gunicorn`. Arreglo:

```bash
flask db heads                                        # debe imprimir UNA línea
flask db merge -m "merge heads" <rev-a> <rev-b>       # revisión vacía que une el grafo
```

El CI (`.github/workflows/ci.yml`) bloquea los PR que dejen más de un head, así que
esto sólo debería aparecer en ramas viejas sin rebasear.

**Con `restart: unless-stopped`, lee el PRIMER intento de migración, no el último.** El
DDL de MySQL no es transaccional: los reintentos fallan con errores secundarios
(`1050 Table already exists`) que tapan la causa raíz.

**Antes de migrar sobre datos que te importen, haz el dump.** Una migración a medias en
MySQL no se deshace sola:

```bash
docker compose -p sunalyze --env-file .env.docker exec -T db \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction sunalyze | gzip > backup.sql.gz
```

## Despliegue en servidor

`documentation/despliegue-hetzner.md` (local, no versionado) cubre servidor, Caddy con
TLS, backups y monitorización. `docs/docker-deploy.md` explica la arquitectura de la
imagen.

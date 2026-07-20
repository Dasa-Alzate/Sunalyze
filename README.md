# Sunalyze

Plataforma SaaS para el **diseño y la legalización de instalaciones solares fotovoltaicas** (mercado español). Backend Flask (API JSON + portal de administración) y SPA React/Vite. Calcula la producción con datos de irradiancia de PVGIS, dimensiona el campo FV y los equipos, y genera la documentación técnica, legal y comercial del proyecto.

## Características

**Diseño y cálculo**
- Producción e irradiancia óptima por ubicación (PVGIS), dimensionamiento del campo y selección de inversor compatible; pérdidas por temperatura/suciedad/cableado.
- Catálogo de equipos (paneles, inversores, **baterías**, cables): propios por organización + catálogos oficiales, con scrapers de catálogos de marca.
- **Baterías y autoconsumo**: dimensionado del banco y estimación del uplift de autoconsumo.

**Documentación**
- Memoria técnica (ITC-BT-40) y diagrama unifilar en PDF (WeasyPrint).
- **Constructor de plantillas de documentos**: banco + editor por secciones con un motor de variables propio y seguro (`{{ entidad.propiedad | filtro }}`), biblioteca por organización (categorías, labels, favoritos), y generación de PDF con la versión de plantilla fijada.

**Negocio**
- **Flujo de legalización**: estados `borrador → en_revision → presentado → aprobado` (+ `rechazado`) con firma de memoria.
- **Análisis financiero**: payback, TIR, VAN, LCOE, CO₂, escenarios contado vs financiado y **subvenciones** (IRPF, IBI, Next Gen); "estudio de ahorro" para el cliente.
- **Posventa**: seguimiento de instalaciones entregadas (estado, mantenimiento, incidencias, rendimiento esperado vs real).

**Plataforma**
- Multi-tenant (organizaciones + roles owner/admin/member); **marketplace de módulos + feature flags**.
- **Portal de superadmin** (Jinja, en subdominio) con MFA/TOTP, allowlist de IP y auditoría.
- **Cumplimiento UE**: RGPD (export + derecho al olvido), endurecimiento de cuentas (lockout, política de contraseñas) y bitácora de auditoría.
- **Productividad**: paleta de comandos (⌘K/Ctrl+K), atajos y consola CLI in-app. **Accesibilidad AA**.

## Arranque rápido con Docker (recomendado — Windows, macOS y Linux)

La forma más simple y segura de tener Sunalyze corriendo: no instala nada en tu
máquina (ni Python, ni Node, ni MySQL), todo vive en contenedores.

**Único requisito:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
(Windows/macOS; en Windows acepta la opción WSL2 que propone el instalador) o
Docker Engine + Compose (Linux).

```bash
git clone <repository-url>
cd Sunalyze
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker exec web flask seed demo
```

> En Windows (cmd) el segundo paso es `copy .env.docker.example .env.docker`;
> en PowerShell, `cp` funciona tal cual.

Abre **http://localhost:8000** e inicia sesión con la [cuenta de prueba](#cuenta-de-prueba).
El stack levanta MySQL + Redis + la app, y aplica las migraciones al arrancar.

- Apagar: `docker compose --env-file .env.docker down` (añade `-v` para borrar también los datos).
- Si prefieres usar una base de datos de tu máquina en lugar de la del compose, define `DATABASE_URL` en `.env.docker` (hay un ejemplo comentado).
- Detalle de despliegue en [`docs/docker-deploy.md`](docs/docker-deploy.md).

## Cuenta de prueba

```bash
flask seed demo                                              # instalación nativa
docker compose --env-file .env.docker exec web flask seed demo   # con Docker
```

Crea (idempotente) la cuenta de desarrollo y los feature flags por defecto:

| Campo | Valor |
|---|---|
| Email | `sunalize_test@sunalize.com` |
| Contraseña | `test123` |
| Rol | superadmin + owner de su organización |

Solo para entornos locales: el comando se niega a correr en producción salvo
que se fuerce con `ALLOW_SEED_DEMO=1`.

## Instalación nativa (sin Docker)

Para trabajar en el código con recarga en caliente. Requisitos:

- **Python 3.12+**
- **Node 18+** (para compilar la SPA)
- **MySQL 8 / MariaDB** — o **SQLite** si no quieres instalar nada: usa `DATABASE_URL=sqlite:///.../dev.db`
- **Librerías de sistema nativas:**
  - WeasyPrint (PDF): Pango/HarfBuzz + fuentes. macOS `brew install pango`; Debian/Ubuntu `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core`. **Windows:** WeasyPrint necesita GTK y suele dar guerra — usa la ruta Docker o trabaja dentro de WSL2 (Ubuntu) siguiendo los pasos de Linux.
  - `mysqlclient` (se compila): `build-essential pkg-config default-libmysqlclient-dev` (Debian/Ubuntu). El runtime usa `PyMySQL`, así que SQLite y MySQL funcionan sin compilar si no instalas `mysqlclient`.

```bash
git clone <repository-url>
cd Sunalyze

# 1) Backend — macOS / Linux / WSL2
python -m venv .venv && source .venv/bin/activate
# 1) Backend — Windows PowerShell
#    python -m venv .venv
#    .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# 2) Frontend (genera frontend/dist/, gitignored; lo sirve Flask)
cd frontend && npm install && npm run build && cd ..

# 3) Entorno
cp .env.example .env        # Windows (cmd): copy .env.example .env — edita los valores (ver abajo)
```

> `frontend/dist/` **no se versiona**: recompílalo con `npm run build` cada vez que cambie el frontend, y como paso de build en el despliegue. Si falta, la raíz muestra un aviso en vez de fallar.

## Configuración (`.env`)

| Variable | Para qué |
|---|---|
| `FLASK_ENV` | `development` o `production`. |
| `SECRET_KEY` | Firma de sesiones. **Obligatoria en producción** (en dev se genera efímera). |
| `DATABASE_URL` | **Obligatoria.** `mysql+pymysql://user:pass@host:3306/sunalyze` o `sqlite:///$PWD/dev.db`. |
| `MFA_ENC_KEY` | Clave Fernet para cifrar el secreto TOTP en reposo (si se omite, se deriva de `SECRET_KEY`). |
| `SERVER_NAME`, `SUPERADMIN_SUBDOMAIN` | Sirven el portal de superadmin en subdominio (`admin.*`). Sin `SERVER_NAME`, el portal queda en `/superadmin`. |
| `SUPERADMIN_IP_ALLOWLIST`, `SUPERADMIN_TRUST_PROXY` | Allowlist de IP del portal (IPs/CIDRs) y confianza en `X-Forwarded-For` tras proxy. |
| `RATELIMIT_STORAGE_URI`, `CACHE_TYPE`, `CACHE_REDIS_URL` | Opcionales: backend Redis para rate-limit/cache compartidos entre workers (por defecto en memoria/proceso). |

## Base de datos (migraciones)

```bash
export FLASK_APP=run     # Windows PowerShell: $env:FLASK_APP = "run"
flask db upgrade         # aplica todas las migraciones (Flask-Migrate/Alembic)
flask seed demo          # cuenta de prueba + flags por defecto (opcional)
```

## Ejecución

**Desarrollo (recarga en caliente)** — dos terminales:
```bash
export FLASK_APP=run && flask run        # API Flask en :5000
cd frontend && npm run dev               # SPA con HMR en :5173 (proxy /api → :5000)
```
Abre `http://localhost:5173`.

> **macOS:** el puerto 5000 lo ocupa el receptor de AirPlay (responde 403 en
> `localhost`). Desactívalo en Ajustes del Sistema → General → AirDrop y Handoff,
> o corre la API en otro puerto: `flask run -p 5001` y
> `FLASK_URL=http://127.0.0.1:5001 npm run dev`.

**Producción (un proceso sirve SPA + API):**
```bash
gunicorn -c docker/gunicorn.conf.py wsgi:app
```

## Comandos CLI (`export FLASK_APP=run`)

```bash
flask seed demo                     # cuenta de prueba local (superadmin) + flags
flask superadmin grant <email>      # conceder acceso de superadmin (bootstrap)
flask superadmin mfa-reset <email>  # reiniciar el MFA de un superadmin
flask superadmin revoke|list
flask scrape list                   # marcas con scraper
flask scrape run <marca> [--dry-run]
flask flags seed                    # sembrar las feature flags por defecto
flask api-map                       # regenerar docs/api-map.md (índice de endpoints)
```

## Feature flags

Capacidades activables por organización (gestión en el portal de superadmin → `/api/admin/flags`; resolución por precedencia user > org > global > default):

| Flag | Capacidad | Default |
|---|---|---|
| `geo_map` | Mapa OSM + geocodificación en el wizard | ON |
| `advanced_analysis` | Métricas/desglose ampliado del dimensionado | OFF |
| `templates` | Constructor de plantillas de documentos | OFF |
| `finance` | Análisis financiero (payback/TIR/VAN/LCOE/CO₂) | OFF |
| `posventa` | Seguimiento de instalaciones tras la entrega | OFF |

## Tests

```bash
# Backend (unittest; requiere DATABASE_URL a sqlite aislada)
export FLASK_APP=run PYTHONPATH=$PWD DATABASE_URL="sqlite:///$PWD/test.db"
flask db upgrade && python -m unittest discover -s tests

# Frontend
cd frontend && npm run lint && npm test    # eslint (incl. jsx-a11y) + vitest (axe)
```

## Estructura del proyecto

```
app/
  __init__.py        # app factory (create_app)
  extensions.py      # db, migrate, csrf, limiter, cache
  config.py / models/ schemas/ (pydantic) routes/ (blueprints) services/ (dominio)
  gateways/          # PVGIS, tokens
  scrapers/          # scrapers de catálogos
  superadmin/        # portal Jinja (subdominio)
  templates/         # Jinja de los PDF (memoria/diagrama)
frontend/src/
  app/ (shell+router)  features/ (dominio)  services/  shared/ (ui+utils)  api/client.js
wsgi.py              # entrypoint de producción (gunicorn + ProxyFix)
docker/              # Dockerfile assets, gunicorn.conf.py, entrypoint
migrations/          # Alembic
```

## API y documentación

- **Mapa de endpoints**: [`docs/api-map.md`](docs/api-map.md) (autogenerado con `flask api-map`) y la convención en [`docs/api-conventions.md`](docs/api-conventions.md). La API es REST (`PATCH` para update; acciones `POST /<recurso>/<id>/<verbo>`).
- **Despliegue**: [`docs/docker-deploy.md`](docs/docker-deploy.md).
- **Seguridad/cumplimiento**: [`docs/security-mfa.md`](docs/security-mfa.md), [`docs/compliance-gdpr.md`](docs/compliance-gdpr.md), [`docs/security-account-audit.md`](docs/security-account-audit.md).
- Investigación y diseño por feature: ver `docs/*-research.md`.

## Licencia

MIT

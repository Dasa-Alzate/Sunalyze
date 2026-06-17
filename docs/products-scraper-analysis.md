# Análisis de viabilidad — scrapers de catálogos de equipos

Rama `products-scrapper`. Objetivo: jobs periódicos que recorran los catálogos de
las **marcas registradas en la BD de equipos** y **creen/actualicen** paneles e
inversores. Este documento evalúa viabilidad (con evidencia real de fetches) y
propone la arquitectura. **No es implementación; es el análisis previo.**

Marcas en la BD hoy: **AIKO, JA Solar, Tensite** (paneles) · **Deye, Fronius, SMA** (inversores).

---

## 1. Hallazgos de la investigación (evidencia)

Hay **tres tipos de fuente**, con viabilidad muy distinta:

| Fuente | Ejemplo verificado | Estructura | Veredicto |
|---|---|---|---|
| **HTML técnico oficial** | Fronius `technical-data/.../primo-5-0-1` | **HTML estático, filas etiquetadas** (MPPT, rango DC, Umpp, corrientes, eficiencia) — sin JS | ✅ Ideal: scrape robusto |
| **PDF datasheet oficial** | Deye `datasheet_sun-60-80k...pdf`, AIKO `wp-content/...pdf` | PDF con tablas; **a menudo multi-modelo** (SUN-60/70/75/80K, AIKO-Gxxx 625-660W) | ⚠️ Viable pero frágil: requiere parser PDF + expansión de familias |
| **Agregador** | ENF Solar `enfsolar.com/pv/inverter-datasheet/...` | Muy estructurado y uniforme entre marcas… | ❌ **403 anti-bot**. ToS prohíbe scraping. Descartado |

Evidencia concreta:
- **Fronius (HTML):** la página técnica devolvió specs en texto plano etiquetado
  (`Max. input voltage: 600 V`, `MPP voltage range: 240 - 480 V`, `Max. efficiency: 96,9 %`).
  Extracción directa y fiable.
- **ENF Solar (agregador):** `HTTP 403 Forbidden` al fetch. Bloquea bots; su ToS
  prohíbe scraping. Atractivo por uniformidad, pero **no es una vía legítima**.
- **Deye (PDF):** el PDF se descarga (253 KB) pero su texto va en streams
  comprimidos → el extractor naíf falla; **hace falta una librería real**
  (`pdfplumber`/`pymupdf`). Además un PDF cubre varios modelos → hay que dividir.

Conclusión: **no existe una fuente única uniforme** que sea legítima. La realidad
es heterogénea (HTML por modelo en unas marcas, PDF multi-modelo en otras, sitios
con CMS antiguos en otras como JA Solar). Esto **manda la arquitectura**: un
**adapter por fuente**, no un scraper genérico.

---

## 2. Arquitectura propuesta

### 2.1 Adapter por marca/fuente (patrón Strategy)
Interfaz común, una implementación por marca apuntando a **su mejor fuente**:
```
class BrandScraper(Protocol):
    brand: str
    def discover() -> list[ProductRef]      # URLs/modelos a recorrer
    def fetch(ref) -> RawDoc                 # HTML o PDF (con cache ETag/Last-Modified)
    def parse(raw) -> list[NormalizedProduct]  # specs crudas → dicts normalizados
```
- `FroniusScraper` → HTML oficial (parser HTML, p. ej. `selectolax`/`lxml`).
- `DeyeScraper`/`AikoScraper`/`JaSolarScraper` → PDF (`pdfplumber`) + expansión de familias.
- Preferir **HTML** siempre que exista; **PDF como fallback** (más frágil, revisar).
- Tensite: marca pequeña → probablemente alta dificultad/datos escasos; candidata a **carga manual**.

### 2.2 Normalización (la capa que de verdad cuesta)
Mapear specs heterogéneas → esquema `Panel`/`Inverter`:
- **Unidades y convención decimal**: los datasheets EU usan **coma** (`96,9 %`) →
  parsear a float. W vs kW, mm vs m, signos de coeficientes de temperatura.
- **Familias multi-modelo** → expandir a SKUs individuales (potencias por bin).
- **Validación**: descartar/relegar a revisión lo que no cuadre (rangos sanos).

### 2.3 Upsert con *provenance* y respeto a ediciones humanas
- Match por clave estable: `(catálogo_oficial_de_la_marca, nombre_modelo_normalizado)`.
- **Provenance** en el equipo: `source`, `source_url`, `external_id`, `scraped_at`.
- **`is_locked`/`manual_override`**: si un humano editó el equipo, el scraper **no
  lo pisa** (o crea una propuesta de cambio). Evita el bug clásico de "el bot
  revierte una corrección manual".
- Cambios → registrar **diff** (enlaza con la futura bitácora de auditoría).

### 2.4 Staging + revisión humana (recomendado)
El scraper **no publica directo** al catálogo oficial. Escribe en una tabla de
staging (`ScrapedProduct`, estado `pending|approved|rejected`); un operador
(super-admin) revisa y aprueba → entonces se hace el upsert real. Para *cambios*
de specs de equipos ya existentes, se puede auto-aplicar con diff + provenance.
Esto protege la calidad de un dato que alimenta cálculos de ingeniería.

### 2.5 Jobs periódicos
- **v1:** comando `flask scrape run [marca] [--dry-run]` + **cron** (frecuencia
  baja, p. ej. semanal). Simple, observable, sin infra nueva.
- **v2:** **Celery beat** (sobre el Redis que ya es dependencia) cuando exista
  worker — encaja con el aislamiento de cómputo pesado ya discutido.
- Cada ejecución crea un `ScrapeRun` (marca, inicio/fin, nº creados/actualizados/
  errores) para trazabilidad.

### 2.6 Cortesía y aspecto legal (no negociable)
- Respetar `robots.txt`, **rate-limit** + backoff, cache condicional (ETag/
  Last-Modified), `User-Agent` identificable, frecuencia baja.
- **Preferir fuentes oficiales** del fabricante; **no** eludir anti-bot de
  agregadores (ENF) ni sus ToS. Las *specs* son datos fácticos, pero el PDF/HTML
  tiene términos de uso: ante duda, fuente oficial + bajo volumen + revisión.

---

## 3. Cambios de modelo (BD)
- `Panel`/`Inverter`: añadir `source`, `source_url`, `external_id`, `scraped_at`,
  `is_locked` (nullable; los equipos manuales quedan con `source='manual'`).
- `ScrapedProduct` (staging): marca, tipo, payload normalizado, `status`, `diff`, `run_id`.
- `ScrapeRun` (auditoría de ejecución): marca, contadores, timestamps, estado.

---

## 4. Fases + POC recomendado
- **POC (bajo riesgo, alta señal):** `FroniusScraper` contra el **HTML oficial**
  (ya verificado extraíble) → normalizar → **upsert en dry-run** al catálogo
  Fronius. Demuestra el pipeline completo sin tocar PDF ni anti-bot.
- **Fase 1:** adapters HTML donde existan + staging + `flask scrape run` + cron.
- **Fase 2:** vía PDF (`pdfplumber`) para Deye/AIKO/JA Solar + expansión de familias.
- **Fase 3:** consola de revisión (aprobar staging), Celery beat, métricas.

---

## 5. Riesgos / límites honestos
- **Fragilidad estructural:** cualquier rediseño del sitio del fabricante rompe su
  adapter → necesita monitoreo y alertas (un adapter caído ≠ silencio).
- **PDF = deuda:** parsing de tablas es brittle; presupuestar revisión humana.
- **Cobertura desigual:** Fronius fácil; Tensite probablemente manual.
- **Legal/ToS:** mantenerse en fuentes oficiales y bajo volumen; documentar la política.
- **Calidad del dato alimenta cálculos:** por eso el staging+revisión no es opcional
  para *altas*; un Voc mal parseado falsea el dimensionado.

**Veredicto:** **viable y con buen ROI vía HTML oficial** (empezando por Fronius),
con PDF como segunda ola y revisión humana como red de seguridad. El agregador
uniforme (ENF) queda descartado por anti-bot/ToS.

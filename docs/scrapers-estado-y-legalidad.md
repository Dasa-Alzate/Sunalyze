# Scrapers de catálogo — estado, arquitectura y análisis legal

Iteración de **2026-07-27** sobre la rama `feature/presupuesto`. Continúa
`docs/products-scraper-analysis.md` (análisis previo) y cierra el punto que allí
quedaba pendiente: *«crawler de discovery real de Fronius (hoy seed de URLs)»*.

Objetivo de la iteración: que los scrapers **descubran todos los modelos que
existan en la fuente** en lugar de recorrer una lista fija, y que extraigan
nombre, parámetros y datasheet.

---

## 1. Estado por frente

| Frente | Estado | Detalle |
|---|---|---|
| Fronius (sitio ES, inversores) | 🟢 **verde** | 90 modelos descubiertos, 87 limpios. En producción. |
| Infraestructura (ABC, caché, lotes, robots) | 🟢 **verde** | Compartida por todos los adapters. |
| Validación de cables | 🟢 **verde** | Alineada con las columnas `NOT NULL` del esquema. |
| Paneles (importador CEC) | 🟢 **verde** | ~3.500 módulos de 19 marcas del mercado ES (§7ter). |
| Baterías (Battery List CEC) | 🟢 **verde** | 374 modelos; voltaje pendiente de revisión (§7ter). |
| Convivencia multi-fuente | 🟢 **verde** | Precedencia fabricante > CEC > distribuidor (§7ter). |
| AutoSolar (señal de mercado ES + datasheet) | 🔴 **bloqueante legal** | Sigue activo por decisión de David; **no publicar a clientes sin revisión legal** (§5). |
| Datasheets de AutoSolar | 🟡 **WIP** | Hoy se hotlinkea su CDN; hay que dejar de hacerlo. |
| Disponibilidad por país (`equipment_markets`) | 🟡 **spec pendiente** | Análisis en §7ter. |

---

## 2. Arquitectura implementada

```
app/scrapers/
  scraper.py     BrandScraper(ABC)     fetch() por defecto; discover()/parse() abstractos
  http.py        conditional_get()     ETag/Last-Modified + huella de contenido
                 plain_get()           listados y sitemaps (sin caché: un 304 aquí
                                       significaría «no hay productos»)
                 ensure_allowed()      robots.txt, con timeout y caché por host
                 html_fingerprint()    texto visible + hrefs, sin tokens volátiles
  sitemap.py     discover_urls()       recorre sitemap-index con filtros follow/keep
  base.py        grab(), grab_range()  extracción por etiqueta con ventana acotada
  acceptance.py  criterios por capas   global → marca → equipo
  service.py     ScraperService.run()  orquestación, upsert, provenance, lotes
  fronius.py     FroniusScraper
  autosolar.py   AutoSolarScraper
```

### Por qué una ABC y no helpers libres

La cortesía con el sitio remoto (User-Agent identificable, pausa, caché
condicional, `robots.txt`) es una **política transversal**, y las políticas
quieren ser correctas por defecto. Con funciones libres, un adapter nuevo que se
olvide de llamarlas funciona igual de bien pero machaca el sitio del fabricante:
fallo silencioso y con daño externo. Con la ABC hereda el comportamiento correcto
sin hacer nada, y para equivocarse tiene que sobrescribir `fetch()` explícitamente.

Los métodos concretos de la ABC **delegan** en funciones libres, de modo que
`conditional_get(url)` y `discover_urls(sitemap, filtro)` siguen siendo
ejecutables desde un shell para depurar una marca sin instanciar nada. La ABC no
guarda estado: `registry.py` instancia los scrapers en tiempo de import.

### Contrato con el orquestador

`fetch()` devuelve `None` para decir «sin cambios, sáltalo». `ScraperService` lo
cuenta como `unchanged` y no llama a `parse`. La entrada de caché **solo se
graba tras un upsert correcto** (`scraper.remember(ref)`), nunca antes: si se
grabara al descargar, un fallo posterior dejaría la URL marcada como vista y el
producto se saltaría para siempre. El sesgo es siempre hacia repetir trabajo,
nunca hacia omitir en silencio.

### Caché condicional

Tres niveles, en orden de coste:

1. `If-None-Match` / `If-Modified-Since` → un `304` evita descargar y parsear.
2. Si el servidor responde `200`, se compara la **huella** del contenido; si
   coincide, se evita parsear y escribir.
3. `--full` ignora ambos y reprocesa todo.

La huella no es el hash del HTML crudo. El CDN de Fronius está balanceado y cada
nodo emite un `ETag` distinto y un cuerpo ligeramente distinto, así que hashear
bytes daba un 19 % de acierto. La huella toma el **texto visible más los
`href`**, descartando `<script>`/`<style>` y colapsando tiradas largas de hex
(tokens CSRF). Acierto medido: **76/90**.

### Commit por lotes

`_upsert` hace `flush()`, no `commit()`. `ScraperService` confirma cada 100
productos almacenados, lo que acorta la ventana en la que el cliente ve un
catálogo a medio actualizar (de la duración entera del barrido a segundos). Un
fallo de lote hace `rollback` y se registra como error: se pierde hasta un lote
de trabajo, nunca la coherencia.

---

## 3. Resultados medidos

### Fronius (sitio español, `es-es/spain`)

```
90 fichas descubiertas → 87 aceptadas · 2 a revisar · 1 bloqueada
0 nombres duplicados
```

| Modelo | power | vmax | y | I entrada | I salida |
|---|---|---|---|---|---|
| Fronius Symo 3.7-3-S | 3.7 kW | 1000 V | 98.0 % | 16.0 A | 5.3 A |
| Fronius Eco 27.0-3-S | 27.0 kW | 1000 V | 98.3 % | 47.7 A | 40.9 A |
| Primo GEN24 10.0 | 10.0 kW | 600 V | 97.3 % | 22.0 A | 45.45 A |

Sin resolver: `Tauro 50-3-D` no publica `vmax` (bloqueada), y `Primo GEN24 8.0/10.0
Plus` no publican eficiencia (entran marcadas). 22 fichas llevan nota de
procedencia porque su `vmax` se tomó de la tensión MPP máxima, que es un valor
**conservador** — nunca superior al límite real de entrada, así que el margen de
compatibilidad que calcula `analysis_service` sale por el lado seguro.

### AutoSolar

```
1.388 fichas descubiertas (388 paneles + 942 inversores + 58 cables)
→ 268 creadas · 5 actualizadas · 28 a revisar · 1.057 bloqueadas
```

El tope anterior era `max_products = 60`, que ni llegaba a los inversores.

### Contraste que importa

| Fuente | Fichas | Utilizables | Tasa |
|---|---|---|---|
| Fronius (fabricante) | 90 | 87 | **97 %** |
| AutoSolar (distribuidor) | 1.388 | 273 | **20 %** |

Un fabricante publica especificaciones canónicas y quiere que se difundan. Un
distribuidor publica lo mínimo para vender. La diferencia de calidad no es
accidental, y —como se ve en §5— apunta en la misma dirección que el análisis
legal.

---

## 4. Defectos encontrados y corregidos

Seis, todos con evidencia reproducible:

1. **`grab` solo probaba la primera aparición de cada etiqueta.** La ficha del
   Fronius Eco tiene un `<h2>` de marketing («proyectos con el *máximo
   rendimiento*») que se comía el match antes de llegar a la tabla:
   17 inversores quedaban sin eficiencia. Ahora se recorren todas las apariciones.

2. **Colisión de etiquetas en los GEN24.** `Corriente de salida CA` casa con dos
   especificaciones distintas: la salida de red y la del **PV Point** (la toma de
   emergencia, 13 A fijos). Todos los Primo daban 13.0 A independientemente de su
   potencia. La etiqueta correcta es `Corriente de salida de CA máxima`.

3. **Trampa de orden de palabras.** En la misma ficha conviven
   `Rendimiento máximo` (rango de tensión MPP, en voltios) y `Máximo rendimiento`
   (eficiencia, en por ciento). Elegir mal el orden deja `y` a nulo en toda la gama.

4. **`_match_by_vitals` podía corromper datos.** El catálogo Fronius tenía 8 filas
   PRIMO introducidas a mano con el mismo `vmax` y las mismas potencias nominales
   que los Symo GEN24 nuevos; con tolerancia del 2 % los emparejaba, y como en ese
   caso se preserva el nombre, el resultado era una fila llamada «Fronius PRIMO
   3.0-1» cargada con especificaciones de un trifásico. `(power, vmax)` no se
   acerca a ser clave única: toda la gama comparte `vmax` y las potencias están
   estandarizadas. **Regla nueva: el emparejamiento difuso solo puede reclamar
   filas que el propio scraper creó** (`source LIKE 'scraper:%'`), nunca dato
   humano. Se conserva el caso legítimo —el mismo producto cuya URL cambia
   upstream— porque esas filas también son del scraper.

5. **Inversores de AutoSolar: 100 % bloqueados, y ya lo estaban antes.**
   `power_from_name` leía cualquier número del título: «Inversor Victron Phoenix
   12V 500VA» daba 12 kW (la tensión de batería) y «TAB 1P 3,6 kW» daba 1 (del
   «1P»). Ahora se lee `potencia de salida continuada`, con parser de miles
   explícito: `'6.500 W'` y `'600 W'` se interpretaban con reglas distintas porque
   `to_float_eu` solo trata el punto como separador decimal. `vmax` sale del
   extremo superior del `rango de funcionamiento del mpp`.

6. **Cables: 58 `IntegrityError` por ejecución.** `acceptance` no tenía reglas para
   `wire`, así que los cables pasaban la validación sin comprobar nada y morían en
   el `INSERT` porque `Wire.corriente` es `NOT NULL`. AutoSolar **no publica lista
   de especificaciones en las páginas de cable**: solo se puede sacar `seccion` del
   título y `material` por heurística. Ahora se bloquean con motivo claro.

También se corrigió un `RobotFileParser.read()` sin timeout, que podía colgar un
barrido indefinidamente si el `robots.txt` de un fabricante no respondía.

---

## 5. Análisis legal

**No es asesoramiento legal.** Es un análisis técnico de la exposición, con la
evidencia recogida durante la implementación. Antes de que estos datos lleguen a
clientes conviene revisión de un abogado de propiedad intelectual.

Las dos fuentes están en posiciones muy distintas y hay que separarlas.

### Fronius — posición sólida

- **Son hechos sobre sus propios productos.** Un `Voc = 44,4 V` no es obra
  protegible por derecho de autor. No se toma prosa comercial ni fotografías.
- **Se respeta `robots.txt`** y se usa **el sitemap que ellos anuncian en él**,
  que es una invitación explícita a rastrear.
- **No se elude nada.** Los endpoints `/productList/productoverview` y
  `/customfields/sortabletablefield/getproducts` están en `disallow` y se
  descartaron; de ahí la decisión de ir por el sitemap.
- **Volumen bajo:** 90 páginas semanales, `User-Agent` identificable con correo
  de contacto, pausa entre peticiones.
- **Interés alineado:** un fabricante publica datos técnicos para que sus equipos
  se especifiquen correctamente.

### AutoSolar — la exposición real

1. **Derecho *sui generis* de base de datos.** Es el riesgo relevante, no el
   derecho de autor. La Directiva 96/9/CE (arts. 133-137 TRLPI) protege a quien
   hizo **inversión sustancial en obtener, verificar o presentar** el contenido, y
   le permite impedir la extracción de una **parte sustancial**. AutoSolar ha
   invertido en *obtener* y homogeneizar especificaciones de decenas de
   fabricantes, que es el tipo de inversión que sí cuenta (el TJUE excluyó en
   *British Horseracing Board*, C-203/02, la inversión en *crear* el dato, no en
   recopilarlo). **1.388 fichas es probablemente una parte sustancial de su
   catálogo**, y el art. 7.5 cubre además la extracción repetida y sistemática de
   partes no sustanciales.
   A favor: *CV-Online Latvia v Melons* (C-762/19, 2021) exige que el acto
   **perjudique la inversión**; Sunalyze no es una tienda que le reste ventas.
   Es un argumento de daño, no un permiso.

2. **La excepción de minería de datos no cubre esto del todo.** El art. 4 de la
   Directiva DSM 2019/790 (RDL 24/2021) permite extracciones para minería —incluso
   comerciales— sobre contenido de acceso lícito, **salvo reserva expresa legible
   por máquina**. Su `robots.txt` declara
   `Content-Signal: ai-train=no, search=yes, ai-input=yes`, que **es** una reserva
   legible por máquina. Y la excepción autoriza copias «durante el tiempo
   necesario para la minería»: un catálogo permanente dentro de un producto
   comercial encaja mal. Minar para analizar no es republicar.

3. **Su `robots.txt` no tiene bloque `User-agent: *`.** Enumera agentes concretos
   (Googlebot, Bingbot, Slurp, Google-Extended, Amazonbot, Applebot-Extended,
   PetalBot) y bloquea a Bytespider. Verificado: nuestro agente **no está
   prohibido** —sin grupo aplicable, la RFC 9309 permite el acceso—, así que
   formalmente se cumple. Pero la estructura del fichero expresa una decisión
   sobre quién entra, y sus tres señales son buscar y responder preguntas, no
   ingerir el catálogo. Se cumple la letra; el espíritu es discutible.

4. **Los PDF de datasheet son un problema de dos capas.** Se guardan URLs de
   `cdn.autosolar.es/...Ficha-Tecnica-*.pdf`: es hotlinking a su CDN (su ancho de
   banda) y el PDF es además obra del fabricante que ellos alojan.

No se localizó su aviso legal en `/aviso-legal` ni `/condiciones-generales`
(404 en ambos), así que **se desconoce qué dicen sus condiciones**. Importa:
*Ryanair v PR Aviation* (C-30/14) estableció que cuando una base de datos no está
protegida, el titular **sí** puede restringir su uso por contrato.

### Lo que no es problema

- **RGPD: no aplica.** No hay dato personal en las especificaciones de un inversor.
- **Acceso ilícito a sistemas (arts. 197 bis / 264 CP):** páginas públicas, sin
  autenticación, sin eludir protecciones, con pausa entre peticiones.

### Recomendación

**Fronius: adelante.** Opcionalmente, un correo a su departamento técnico
convierte la duda residual en un permiso explícito.

**AutoSolar: no publicar a clientes sin revisión legal.** Tres salidas:

1. **Pedir permiso o un feed.** Puede interesarles: si Sunalyze dimensiona con su
   catálogo, dirige compras hacia ellos.
2. **Sustituirlo por adapters de fabricante** *(preferida)*. Es lo que ya proponía
   el análisis previo, elimina el riesgo de raíz y da mejor dato — el 20 % de
   aprovechamiento indica que AutoSolar tampoco aporta tanto.
3. **Mantenerlo solo como herramienta interna** de investigación.

En cualquier caso, dejar de hotlinkear sus PDF.

---

## 6. Baterías: sin fuente viable hoy *(RESUELTO en §7ter con la Battery List de la CEC — se conserva el análisis por contexto)*

Ninguna de las dos fuentes permite ingerir baterías:

- **Fronius no publica fichas por modelo.** La página `fronius-reserva` no
  contiene ningún dato técnico («Elige el producto que deseas» y navegación); los
  modelos (Reserva 6.3, 9.5, 12.6…) solo aparecen dentro de una tabla de
  compatibilidad. El único producto hoja de esa categoría es una batería **BYD**,
  no Fronius.
- **AutoSolar tiene ~780 baterías** en 37 páginas, con `amperios-hora`, `voltaje` y
  `energía útil almacenada`. De ahí salen `capacity_kwh` (Ah × V / 1000), `voltage`
  y `dod`. Pero **`power_kw` no lo publica**, y es `NOT NULL` en `Battery` y campo
  vital en `acceptance`.

Opciones, con su coste:

| Opción | Coste | Riesgo |
|---|---|---|
| `power_kw` opcional + disclaimer en el catálogo | Migración + revisar qué cálculos lo usan | Bajo, si se marca `needs_review` |
| Dejarlas fuera | Ninguno | El catálogo no crece |
| Adapters de fabricante (Pylontech, BYD, Huawei) | Un adapter por marca | Ninguno, y da el dato completo |
| Derivar de una tasa C asumida | Bajo | **Inaceptable**: inventa dato de ingeniería |

El enrutado ya está listo en el orquestador (`Battery` en `_MODEL` **y** en
`_VITAL_NUM` — lo segundo era un `KeyError` latente), así que en cuanto haya
fuente funciona sin más cambios.

---

## 7. Marcas presentes y hoja de ruta

Distribución real de lo ingerido desde AutoSolar, que es la mejor guía de qué
marcas merecen un adapter propio:

| Paneles | n | | Inversores | n | | Baterías | n |
|---|---|---|---|---|---|---|---|
| Tensite | 60 | | Fronius | 92 | | *(ninguna ingerida)* | 0 |
| JA Solar | 32 | | Tensite | 8 | | | |
| ERA | 13 | | Deye | 7 | | | |
| Aiko | 11 | | Suntaic | 7 | | | |
| Tongwei | 8 | | SMA | 6 | | | |
| Silicon Valen | 8 | | Huawei | 6 | | | |
| LONGi | 7 | | Growatt | 2 | | | |
| Eurener | 6 | | Kostal | 2 | | | |
| Eastech | 4 | | Ingeteam | 1 | | | |
| Solmax | 4 | | | | | | |
| Risen | 1 | | | | | | |

`Tensite` es marca propia de AutoSolar: no tiene fabricante al que ir.

### Sondeo de crawlabilidad (2026-07-27)

| Marca | Uso | HTTP | robots.txt | Sitemap | Veredicto |
|---|---|---|---|---|---|
| **JA Solar** | paneles | **406** | permite | — | 🔴 WAF rechaza el agente |
| LONGi | paneles | 200 | permite | `sitemapindex.xml` | candidato |
| Aiko | paneles | 200 | permite | `wp-sitemap.xml` | candidato |
| Trina Solar | paneles | 200 | permite | `sitemap_index.xml` (20) | candidato |
| Canadian Solar | paneles | 200 | permite | `wp-sitemap.xml` | candidato |
| Jinko | paneles | 200 | sin robots (404) | — | a investigar |
| Risen | paneles | timeout | — | — | a reintentar |
| **Pylontech** | baterías | 200 | permite | `sitemap.xml` | candidato |
| BYD Battery-Box | baterías | 200 | sin robots (404) | — | a investigar |
| Huawei | ambos | 200 | permite | — (15 PDF en portada) | probable vía PDF |
| **Top Cable** | cables | 200 | permite | `sitemap_index.xml` | candidato |
| SMA | inversores | 200 | permite | 4 sitemaps | candidato |
| Deye | inversores | 200 | permite | — | a investigar |
| Ingeteam | inversores | 200 | permite | — | a investigar |

**JA Solar responde `406 Not Acceptable`** a nuestro `User-Agent`: es un WAF
filtrando clientes no-navegador. Es la misma señal anti-bot por la que se descartó
ENF Solar en el análisis previo, así que **no se elude**: queda bloqueado hasta
que exista otra vía (contacto con el fabricante, o su sitio regional europeo).

### Prioridad propuesta

1. **Cables — Top Cable.** Fabricante español que publica tablas de intensidad
   admisible, justo el campo (`corriente`) que hace que los 58 cables de AutoSolar
   se bloqueen. Desbloquea el catálogo de cables por completo.
2. **Baterías — Pylontech.** Publica corriente de carga/descarga, es decir el
   `power_kw` que falta en §6. Desbloquea baterías sin necesidad de migración ni
   disclaimer.
3. **Paneles chinos — Aiko, Trina, LONGi, Canadian Solar.** Los cuatro con sitemap
   accesible. Aiko y Canadian Solar son WordPress (`wp-sitemap.xml`), lo que suele
   implicar HTML estático y estructura uniforme.
4. **Inversores — SMA**, y después Deye / Ingeteam / Kostal.

### Hallazgo decisivo: los fabricantes publican en PDF, no en HTML

Se sondearon las fichas de producto reales (no la portada) de los cuatro
candidatos mejor situados:

| Marca | Página probada | Tablas HTML | Voc/Isc/Intensidad en texto | PDF por ficha |
|---|---|---|---|---|
| Top Cable | `/es/cable/powerflex-rv-k` | 0 | no | **3** |
| Aiko | `/es/products/stellar-1n+72-dual-glass` | 0 | no | **2** |
| Pylontech | `/products/forceh3` | 0 | no | — (JS, 500 car. de texto) |
| JA Solar | — | — | — | WAF responde 406 |

Top Cable tiene 106 fichas en `/es/cable*` y Aiko 24 en `/es/products/*`, con
sitemap accesible y `robots.txt` permisivo: **el descubrimiento es viable, la
extracción no**. Las especificaciones viven en los datasheet PDF; Aiko incluso
expone un «Centro de recursos — Hojas de datos descargables». Pylontech renderiza
sus fichas con JavaScript.

**Conclusión: Fronius era la excepción, no la regla.** No se puede ampliar el
catálogo añadiendo más adapters HTML. La pieza que desbloquea *simultáneamente*
paneles, paneles chinos, baterías y cables es una sola: **el pipeline de ingesta
de PDF** (la «fase 2» del análisis previo).

### El pipeline de PDF como único desbloqueo

Lo que hace falta:

1. **Dependencia nueva:** `pdfplumber` o `pymupdf`. Hoy solo hay `pikepdf`
   (10.5.1), que fusiona pero no extrae texto.
2. **Extracción de tablas** del datasheet a pares etiqueta/valor, reutilizando
   `grab`/`grab_range` sobre el texto resultante.
3. **Expansión de familias multi-modelo:** un PDF suele cubrir varias potencias
   (p. ej. `STELLAR 1N+72 635W-660W` son 6 SKU en un documento). Hay que dividir
   por columnas de bin de potencia.
4. **Descubrimiento del PDF:** ya resuelto por sitemap + `//a[@href$=".pdf"]` en
   la ficha.

Ventaja legal añadida: el datasheet del fabricante es **la fuente más limpia de
todas** — hechos sobre sus propios productos, publicados expresamente para que se
especifiquen, y de descarga libre. Resuelve de paso el problema de hotlinking del
§5, porque el PDF pasa a venir del fabricante y no del CDN del distribuidor.

Coste estimado: es su propia iteración, no un añadido a esta.

---

## 7bis. Existe un catálogo público centralizado: las listas CEC

**Hallazgo que reordena la prioridad.** No hace falta scrapear fabricante por
fabricante para paneles: la **California Energy Commission** mantiene listas
regulatorias de equipos homologados, y **NREL las distribuye con SAM** como CSV
planos en GitHub.

| Fichero | Filas | Tamaño |
|---|---|---|
| `deploy/libraries/CEC Modules.csv` | **21.677 módulos** (9.868 ≥ 400 Wp) | 6,1 MB |
| `deploy/libraries/CEC Inverters.csv` | **2.343 inversores** | 380 KB |
| `deploy/libraries/Sandia Modules.csv` | 523 módulos | 190 KB |

Repositorio: `github.com/NREL/SAM`, rama `develop`. Verificado HTTP 200 el
2026-07-27.

### Mapeo al esquema (verificado, no supuesto)

Las 30 columnas cubren `Panel` casi al completo:

| Sunalyze | Columna CEC |
|---|---|
| `nombre` | `Name` |
| *(marca)* | `Manufacturer` |
| `power` | `STC` |
| `voc` | `V_oc_ref` |
| `vmp` | `V_mp_ref` |
| `imp` | `I_mp_ref` |
| `isc` | `I_sc_ref` |
| `height` / `width` | `Length` / `Width` (metros → mm) |
| `tcv` | `beta_oc` |
| `tcp` | `gamma_pmp` |
| `t_noct` | `T_NOCT` |
| `y` | `STC / A_c / 10` |

Ejemplo real: `JA Solar JAM5-72-165` → STC 165, Voc 44.79, Vmp 36.2, Imp 4.56,
Isc 5.03, 1.58 × 0.808 m, beta_oc −0.1433, T_NOCT 46.1.

Cobertura de marcas chinas (módulos ≥ 400 Wp): Jinko 400, CSI Solar 336,
Runergy 228, Vietnam Sunergy 581, Qcells 336, Phono 195… y en el total,
JA Solar 624, Trina 2.844, LONGi 520, Risen 424.

### Por qué es la mejor fuente disponible

- **Legalmente limpia**: dato regulatorio de un organismo público estadounidense,
  redistribuido por NREL (SAM es BSD-3). Sin `robots.txt`, sin ToS, sin derecho
  *sui generis*, sin anti-bot. Desaparece por completo el §5.
- **Un `GET` sustituye a N scrapers**: un CSV de 6 MB en lugar de 1.388 peticiones.
- **25× más paneles** que AutoSolar (21.677 frente a 388) y con parámetros
  completos, incluidos coeficientes de temperatura que AutoSolar nunca publica.

### Límites honestos

1. **Es la lista californiana.** Para **paneles** casi no importa: un JA Solar de
   550 Wp es el mismo módulo en todo el mundo. Para **inversores sí importa**: las
   entradas son variantes de red estadounidense (`{208V}`, `{240V}`), no los
   modelos 230/400 V europeos. **Por eso el scraper de Fronius ES sigue siendo
   necesario** y no lo sustituye.
2. **No hay baterías.** Confirmado: el directorio de librerías de SAM no incluye
   catálogo de producto de baterías (`BatteryStateful` es configuración de modelo).
3. **No hay cables** — y no es un problema de datasheet: la intensidad admisible
   sale de tablas normativas (IEC/UNE-HD 60364-5-52), no de una ficha de
   fabricante. Sunalyze ya tiene `calculate_section` para eso.
4. **No trae la URL del datasheet PDF.** Para los parámetros es mejor que el PDF;
   pero la memoria técnica fusiona datasheets con `pikepdf`, y ese documento sigue
   habiendo que obtenerlo del fabricante. Son dos necesidades distintas.
5. **Los nombres de fabricante son razones sociales**, no marcas comerciales:
   «CSI Solar Co Ltd» (= Canadian Solar), «Jinko Solar Co Ltd», «Qcells North
   America». Hay que ampliar `KNOWN_BRANDS` en `brands.py` con alias, o se crearán
   catálogos llamados «Vietnam Sunergy Joint Stock Company».
6. **Cola histórica**: hay módulos de 165 Wp de 2010. Filtrar por `STC` y/o por la
   columna `Date`.

### Encaje en la arquitectura actual

Encaja en la ABC sin cambios: `discover()` descarga el CSV y devuelve una ref por
fila, `fetch()` no hace red (el CSV ya está en memoria) y `parse()` mapea columnas.
Reutiliza `acceptance`, el upsert con provenance y el commit por lotes tal cual.
Es **horas de trabajo, no una iteración** — al contrario que el pipeline de PDF.

---

## 7ter. Iteración autónoma (noche del 2026-07-27)

Trabajo realizado en modo autónomo por encargo de David: implementar el CEC sin
cerrar AutoSolar, resolver la convivencia de fuentes, buscar solución de
baterías y analizar «disponibilidad en España».

### Importador CEC de módulos (`flask scrape run cec`)

`app/scrapers/cec.py`. Un GET al CSV de NREL (con caché condicional: si el CSV
no cambió, `discover()` devuelve vacío) → filtro por marca y `STC ≥ 350 W` →
mapeo de columnas. **3.522 módulos de 19 marcas** del mercado español: Jinko 647,
Qcells 498, Canadian Solar 384, Trina 370, Hyundai 256, Phono 253, REC 176,
LONGi 175, ZNShine 157, Risen 126, JA Solar 107… y Exiom (fabricante español) 8.
Aceptación offline: 3.521 de 3.522.

Decisiones dentro del scraper:
- `nombre` se reescribe de razón social a marca («CSI Solar Co Ltd CS3L-350MS» →
  «Canadian Solar CS3L-350MS»); alias en `brands.py`.
- `tcv = beta_oc / voc × 100` (la CEC da V/°C; el modelo espera %/°C **negativo**,
  como exige la fórmula de `analysis_service.py:150`). `tcp = gamma_pmp` directo.
  Valores resultantes verificados en rango físico (−0.26…−0.38 %/°C).
- `y = STC / A_c / 10`. Dimensiones m → mm.
- **No se importan los inversores CEC**: son variantes de red US (208/240 V).

### Convivencia de fuentes: precedencia + el bug que encontró

`source` ahora identifica **al scraper**, no a la marca (`scraper:cec`,
`scraper:autosolar`). Prioridades: fabricante (fronius) 30 > regulatorio (cec) 20
> distribuidor (autosolar y los `scraper:<marca>` históricos) 10.

- Fuente entrante con prioridad **menor** que la dueña de la fila: solo **rellena
  huecos** (p. ej. AutoSolar aporta `datasheet` a una fila CEC), nunca pisa, y no
  toca provenance.
- Prioridad **mayor**: pisa specs y asume la propiedad (`source`, `external_id`);
  si el match fue por vitales, **conserva el nombre** — así una ficha creada por
  AutoSolar mantiene su nombre comercial español con specs CEC debajo.

**El primer run real del CEC corrompió datos y obligó a dos fixes.** Con 3.522
módulos en un catálogo denso, la tolerancia del 2 % en `_match_by_vitals`
fusionaba bins consecutivos (550 vs 555 W = 0,9 %): 3.279 «updates» eran
variantes machacándose en cadena, y varias filas de AutoSolar quedaron con
nombre de un producto y specs de otro. Arreglos: tolerancia **2 % → 0,5 %** (los
bins van de 5 en 5 W) y un **guard temporal** — el match por vitales solo puede
reclamar filas de runs anteriores (`scraped_at < inicio del run`), nunca
hermanas del mismo barrido. Datos saneados borrando `scraper:cec` y purgando la
caché de AutoSolar para reconstruir. Riesgo residual documentado: dos variantes
con specs eléctricos *idénticos* (p. ej. bifacial `-AG` vs estándar) que
aparezcan en runs distintos podrían aún fusionarse.

### Baterías: resueltas con la Battery List de la CEC

`app/scrapers/cec_battery.py` (`flask scrape run cec-baterias`). El portal
`solarequipment.energy.ca.gov` publica un Excel con **977 baterías** (el endpoint
rechaza HEAD pero sirve GET). Trae justo el campo que ninguna otra fuente
publicaba: **Maximum Continuous Discharge (kW) → `power_kw`**, más capacidad,
tecnología y eficiencia round-trip. Marcas del mercado español: **Pylontech 237,
Deye 44, Growatt 28, Dyness 24, BYD 21, GoodWe 12, LG 6, SolaX, FoxESS, EcoFlow,
Tesla**. `openpyxl` ya estaba en requirements: sin dependencia nueva.

Resultado real: **374 baterías creadas** (había 2). Contrapartida: la lista no
publica el **voltaje nominal** — el espejo exacto del problema con AutoSolar
(que tenía voltaje pero no potencia). Decisión: migración `c4d6e8f0a2b4` vuelve
`batteries.voltage` nullable, se saca de los vitales, y toda batería sin voltaje
entra `needs_review` con nota «la lista CEC no publica el voltaje nominal;
verificar en el datasheet del fabricante antes de dimensionar». El voltaje se
extrae del nombre del modelo solo cuando el fabricante lo incluye; **nunca se
deriva** (regla: no inventar dato de ingeniería). La creación manual por API
sigue exigiendo voltaje (`crud.py`).

### Disponibilidad en España: análisis

El CEC dice «homologado en California», no «se vende en España». AutoSolar es
la señal de mercado español que interesa. Opciones evaluadas:

| Opción | Coste | Valoración |
|---|---|---|
| A. Columna `available_es` alimentada por AutoSolar | Migración + UI | Falsos negativos masivos: que AutoSolar no lo venda no significa no disponible |
| B. Tabla `equipment_markets` (equipo × país × fuente) | Spec propio | La correcta a largo plazo; escala a más países y más distribuidores |
| C. No modelar nada: la unión por vitales ya enlaza ambas fuentes | 0 | Lo que queda implementado hoy |
| D. Catálogo transversal «Mercado España» | Rompe el modelo catálogo=marca | Descartada |

**Implementado: C.** El cruce por vitales une la ficha AutoSolar (nombre
comercial español + datasheet + señal de disponibilidad implícita) con los specs
CEC. **Recomendación: B como spec de producto** cuando haya más de un
distribuidor — la fila de AutoSolar en `equipment_markets` diría «disponible en
ES según autosolar.es a fecha X», que es la semántica honesta.

Para baterías/EU no existe hoy equivalente público del CEC (el pasaporte europeo
de baterías es 2027+; EPREL no cubre estacionarias) — no verificado
exhaustivamente, marcado como asunción.

### Resultado final medido (tras el rebuild con los fixes)

| Tabla | Antes de la iteración | Después |
|---|---|---|
| Paneles | 163 | **3.674** (3.522 CEC + 152 AutoSolar) |
| Inversores | 135 | 207 |
| Baterías | 2 | **376** |

El cruce entre fuentes produjo **9 fusiones**, todas legítimas y verificadas una
a una: fichas de AutoSolar (nombre comercial español conservado) enriquecidas
con los specs CEC del bin exacto de potencia — p. ej. «Panel Solar 405W Deep
Blue 3.0 JA Solar Mono» quedó unida a `cec/JA Solar JAM54D30-405/MB` con
`voc=37.23` y `tcv=-0.248`, coeficiente que AutoSolar nunca publica. El cruce es
pequeño porque exige vitales completos por ambas partes y AutoSolar rara vez
publica los cuatro; crecerá si AutoSolar mejora sus fichas, y no es dañino que
no crezca: ambas filas coexisten en el mismo catálogo de marca.

Suite de tests: 373, con 1 fallo preexistente ajeno
(`test_three_svgs_byte_identical`, verificado idéntico sobre HEAD limpio).

---

## 7quater. Titularidad del catálogo como activo (2026-07-28)

El razonamiento del §5 aplicado a favor: si Sunalyze invierte en **obtener,
verificar y presentar** datos que no ha creado (fabricantes, listas CEC), esa
compilación es una base de datos propia protegida por los arts. 133-137 TRLPI y
la Directiva 96/9/CE. El método —manual o automatizado— es jurídicamente
irrelevante; lo que cuenta es que la inversión sea sustancial y que la
**procedencia esté limpia**: una base derivada de AutoSolar no se «lava»
reclamando derecho propio, porque los dos derechos conviven.

Implementado para que el activo sea real y defendible:

1. **Traza de verificación.** `verified_by` / `verified_at` en `ProvenanceMixin`
   (migración `d5e7f9a1b3c5`, las cuatro tablas de equipos). `mark_verified()` se
   dispara al editar por API (`crud.py`), que es el acto humano de verificación.
   La «inversión en verificación» que pondera la ley pasa a ser un dato auditable
   en lugar de una afirmación.
2. **`robots.txt` diferenciado** en `frontend/public/` (servido vía `serve_spa`;
   el Dockerfile compila el frontend, así que llega a producción). Política por
   finalidad, no por permisividad: `Allow` en landing y legal, `Disallow` en
   `/app/`, `/api/`, `/superadmin`, `/imprimir/` y en las rutas con token en la
   query (`/reset-password`, `/invitacion`, `/verificar`), más
   `Content-Signal: ai-train=no, search=yes, ai-input=yes` — sí a que nos
   descubran y nos citen, no a que nos destilen.
3. **Reserva expresa en `/legal/terminos`** (`Legal.jsx`): sección nueva de
   titularidad de la base de datos, con la reserva del art. 4 de la Directiva
   (UE) 2019/790 y art. 67 TRLPI, remitiendo al `robots.txt`. Reconoce
   explícitamente que los datos individuales son hechos no apropiables y que los
   derechos de los fabricantes sobre sus marcas y documentación quedan a salvo.
   Añadido también un aviso de que los registros `needs_review` pueden estar
   incompletos y deben verificarse contra la ficha del fabricante.
   **Pendiente de revisión por abogado.**
4. **Severabilidad operable.** `flask scrape sources` audita procedencia,
   verificación y filas a revisar por fuente; `flask scrape purge-source <source>`
   permite retirar quirúrgicamente todo lo derivado de una fuente concreta si una
   revisión legal lo exigiera.

Auditoría de procedencia el 2026-07-28: **0 filas scrapeadas sin `source_url` ni
`external_id`** en las cuatro tablas. Reparto: 3.522 `scraper:cec`,
375 `scraper:cec-baterias`, 259 `scraper:autosolar`, 91 `scraper:fronius`,
10 `manual`. La migración de «`source` = marca» a «`source` = scraper» quedó
consistente tras el rebuild.

Nota honesta sobre el alcance del derecho: buena parte del catálogo es CEC, o sea
dominio público. La protección recae sobre la selección, verificación y
normalización, no sobre el dato — es legítima pero **fina**, y se refuerza con
cada capa de enriquecimiento propio (nombres comerciales españoles,
disponibilidad de mercado, verificación humana registrada).

---

## 8. Operación

```bash
flask scrape list                      # fuentes registradas
flask scrape run fronius               # inversores EU (sitio español de Fronius)
flask scrape run cec                   # ~3.500 paneles (listas CEC vía NREL)
flask scrape run cec-baterias          # ~380 baterías (Battery List de la CEC)
flask scrape run autosolar             # distribuidor ES (señal de mercado + datasheet)
flask scrape run fronius --dry-run     # no escribe; reporta qué haría
flask scrape run autosolar --limit 20  # acota para pruebas
flask scrape run fronius --full        # ignora la caché condicional
flask scrape run autosolar --quiet     # solo el resumen
flask scrape sources                  # auditoría de procedencia por fuente
flask scrape purge-source scraper:autosolar   # retirada quirúrgica de una fuente
```

Orden recomendado del cron semanal: `autosolar` → `cec` → `cec-baterias` →
`fronius`. AutoSolar primero para que las fichas nuevas del mercado español
existan cuando el CEC las reclame y mejore.

Cron semanal previsto (madrugada de domingo). Cada ejecución registra un
`ScrapeRun` con contadores y notas.

---

## 9. Decisiones pendientes

1. **AutoSolar**: permiso, sustitución por fabricantes, o uso interno. Bloquea las
   baterías y los datasheets.
2. **`power_kw` de baterías**: volverlo opcional con disclaimer, o esperar a los
   adapters de fabricante.
3. **Datasheet en cables**: `Wire` no tiene columna `datasheet`; requiere migración
   si se quiere.
4. **Overlay comercial del marketplace** *(spec aparte, ya acordado)*: hoy
   `precio_unitario` vive en la fila global compartida y es editable por cualquier
   inquilino, lo que filtra precios entre organizaciones y congela la fila frente
   al scraper. Detalle y arquitectura acordada en la nota de memoria
   `overlay-comercial-marketplace`.

# Research — Disposición de paneles sobre PNOA + Presupuesto avanzado

Conocimiento de dominio verificado (2026-07) para las features de disposición de
paneles y presupuesto. Los endpoints se comprobaron en vivo con `curl`.

## Ortofoto oficial: PNOA Máxima Actualidad (IGN)

Servicio público, gratuito, sin API key. Resolución 25 cm. Licencia CC-BY 4.0 —
atribución obligatoria: **«© Instituto Geográfico Nacional de España (PNOA)»**.

### WMS (para el render servidor — imagen estática por bbox)

```
GET https://www.ign.es/wms-inspire/pnoa-ma
  ?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap
  &LAYERS=OI.OrthoimageCoverage&STYLES=
  &SRS=EPSG:4326&BBOX=lng_min,lat_min,lng_max,lat_max
  &WIDTH=1024&HEIGHT=1024&FORMAT=image/jpeg
```

- Verificado: 200 `image/jpeg`, ortofoto real (Alicante, bbox 0.002°).
- Con `VERSION=1.1.1` el eje del BBOX es `lng,lat` (en 1.3.0 + EPSG:4326 sería
  `lat,lng`); se fija 1.1.1 para evitar la trampa del orden de ejes.
- Píxel cuadrado en metros: `WIDTH/HEIGHT = (Δlng·cos φ)/Δlat`.

### WMTS (para los tiles de Leaflet en el paso del wizard)

```
https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile&version=1.0.0
  &layer=OI.OrthoimageCoverage&style=default&format=image/jpeg
  &tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}
```

- Verificado en z=19 y z=20 (200 `image/jpeg` 256×256). `maxNativeZoom: 20`,
  Leaflet puede sobreescalar hasta 22 para trabajar cómodo sobre un tejado.
- Compatible con `L.tileLayer` estándar (plantilla `{z}/{x}/{y}`), cacheable.

## Parcelario: WMS de Catastro

```
GET https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx
  ?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Catastro&STYLES=
  &SRS=EPSG:4326&BBOX=lng_min,lat_min,lng_max,lat_max
  &WIDTH=1024&HEIGHT=1024&FORMAT=PNG&TRANSPARENT=TRUE
```

- Verificado por **https** (sin mixed content en la SPA): 200 `image/png`
  paletizado con transparencia. Se superpone sobre la ortofoto.

## CSP

Los tiles los carga Leaflet como `<img>` → basta ampliar `img-src` en
`app/security_headers.py` con `https://www.ign.es` y
`https://ovc.catastro.meh.es`. El render servidor no pasa por CSP, y el plano
embebido en la memoria usa `data:` URI (ya permitido).

## Geometría de la retícula

### Conversión grados↔metros (equirectangular local)

Para extensiones de tejado (<100 m) el error es despreciable:

```
m_por_grado_lat = 111_320
m_por_grado_lng = 111_320 · cos(lat₀)
```

Se trabaja en un plano local ENU centrado en el tejado; la retícula se genera en
metros y se convierte a lat/lng solo para persistir y dibujar.

### Separación entre filas (auto-sombreado) — criterio IDAE

Del Pliego de Condiciones Técnicas del IDAE (instalaciones conectadas a red):
la distancia libre entre filas para garantizar 4 h de sol en el solsticio de
invierno es

```
d = h / tan(61° − latitud)      con h = L · sin β
```

donde `L` es el largo del panel y `β` su inclinación. El paso de fila (pitch)
es `L·cos β + d`.

- Instalación **coplanar** (pegada a cubierta): las filas no se sombrean entre
  sí → separación puramente mecánica (~2 cm entre marcos).
- Instalación **inclinada sobre horizontal**: β = `beta_optimal` del análisis y
  se aplica la fórmula IDAE. La huella en planta de cada panel es `L·cos β`.

### Rotación por azimut

La retícula se rota por el azimut del proyecto (180° = sur, convención del
wizard). Rotación 2D estándar alrededor del centroide del polígono; el norte
del plano permanece arriba (lat/lng), lo que gira son las filas de paneles.

### Tests de pertenencia

- Punto-en-polígono: ray casting sobre lat/lng (el error de proyección local es
  irrelevante a esta escala).
- Panel válido: sus 4 esquinas y su centro dentro del polígono de cubierta y
  fuera de todos los polígonos de exclusión.

## Render del plano en servidor

Mismo pipeline que los esquemas eléctricos: SVG → `wrap_plan_sheet` (marco
doble + cajetín REBT/UNE/RD 244) → `fit_to_mm` → inline en la plantilla
WeasyPrint. La ortofoto va como `<image href="data:image/jpeg;base64,…">`
dentro del SVG, con el polígono, la retícula, la escala gráfica y el norte
dibujados como vectores encima.

- `requests` con `timeout=8` y fallback: si el WMS no responde, la memoria se
  genera sin plano (sección condicional) y se registra warning.
- Cache de las respuestas WMS con la extensión `cache` (clave = bbox+tamaño,
  TTL 30 días) — la vista previa de la memoria se regenera a menudo y no debe
  golpear al IGN en cada tecla.
- Dos planos: **PLANO DE SITUACIÓN Y EMPLAZAMIENTO** (bbox ancho ~300 m,
  crosshair en el emplazamiento, parcelario catastral superpuesto) y **PLANO DE
  DISPOSICIÓN DE PANELES** (bbox ceñido al tejado + retícula).

## Presupuesto — dominio

- IVA aplicable: 21 % general · 10 % vivienda (obras de renovación/eficiencia
  en vivienda >2 años) · 4 %/0 % casos especiales; selector ya existente.
- Inflaciones (requisito): el precio final de una partida de equipo es
  `precio_tarifa · (1 + inflación_org/100) · (1 + inflación_equipo/100)`,
  redondeado a 2 decimales **al pre-generar**. Las inflaciones no aparecen como
  concepto en el presupuesto: solo alteran el precio unitario final.
- Mano de obra parametrizada por organización: importe fijo de puesta en
  marcha + €/módulo montado → una única partida en el capítulo 3.
- Líneas personalizadas por organización: plantilla de partidas propias
  (capítulo, descripción, unidad, cantidad, precio) que se añaden en cada
  pre-generación.

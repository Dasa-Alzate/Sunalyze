# Disposición de módulos — teoría, cálculos e implementación

Documento de **2026-07-29**. Cubre la geometría del posicionador: marcos de
referencia, retícula, sombras (entre filas y por obstáculos), sistemas de
anclaje, función objetivo y el plan de implementación sobre el código actual.

Complementa `docs/disposicion-presupuesto-research.md`, que documenta las
fuentes cartográficas (PNOA, Catastro) y sigue vigente.

---

## 1. Marcos de referencia

El motor trabaja en un plano local métrico, no en grados. `localConverter`
(`layoutEngine.js:6`) fija un origen y convierte:

```
x_este  = (lng − lng₀) · 111320 · cos(lat₀)
y_norte = (lat − lat₀) · 110574
```

Aproximación plana válida a escala de tejado (errores por debajo del
centímetro en decenas de metros). Todo el cálculo geométrico ocurre en este
plano; la conversión a lat/lng solo se hace al pintar.

---

## 2. La retícula y los dos ángulos que hoy están confundidos

### El hallazgo

`PanelLayout.jsx:62` hace:

```js
const gridAzimut = coplanar ? (Number(azimut) || 180) : 180
```

La rotación de la retícula **no es un parámetro libre**: en coplanar hereda el
azimut del tejado y en cubierta plana está fijada a 180°. Si los bordes de una
cubierta plana no van norte-sur, el enrejado la cruza en diagonal y se
desperdicia superficie.

### La distinción correcta

Son **dos ángulos con consecuencias distintas**:

| Ángulo | Determina | ¿Libre? |
|---|---|---|
| **Azimut del módulo** (γ) | Hacia dónde mira la normal → irradiación | Coplanar: no, lo fija el faldón. Plana: sí |
| **Rotación de filas** (θ) | Cómo se empaqueta la retícula → capacidad | **Siempre libre** |

Y de ahí salen **dos regímenes de optimización**:

**Régimen coplanar — la rotación es gratis.** Los módulos van tumbados en el
plano del faldón. Girar el enrejado *dentro* de ese plano no cambia la normal
del módulo: ni β ni γ se mueven, la irradiación es idéntica. La rotación es
puramente un problema de empaquetado y se puede optimizar sin coste.

**Régimen cubierta plana — la rotación cuesta.** Las estructuras inclinadas
giran con las filas, su γ cambia y la producción baja. Hay un compromiso real
que hay que cuantificar y mostrar.

### Sobre «inclinación en x-z e y-z»

Cualquier plano en el espacio tiene **2 grados de libertad**, y el par
(β, γ) los cubre por completo: un módulo «inclinado en x-z y en y-z» es
exactamente un módulo con cierta inclinación y cierto azimut. Mantener dos
ángulos de inclinación por separado sobreparametriza e invita a estados
inconsistentes. `solar_geometry.incidence_cosine(sun, β, γ)` ya trabaja con el
par correcto.

---

## 3. Optimización de la fase de la retícula

Además de la rotación, la retícula tiene una **fase**: el desplazamiento
(δx, δy) del enrejado respecto al polígono. Hoy queda determinada por el
`origin` y nunca se optimiza, así que la capacidad depende de dónde cayó la
retícula por casualidad.

La fase es periódica con periodo (pitchX, pitchY), de modo que basta muestrear
un periodo:

```
para θ en 0..175 paso 5°:
  para orientación en {retrato, paisaje}:
    para δx en 0..pitchX paso pitchX/8:
      para δy en 0..pitchY paso pitchY/8:
        contar celdas válidas
```

72 × 2 × 8 × 8 = 9.216 evaluaciones. Cada una es un recuento sobre la caja
envolvente; con la poda de la sección 7 corre en decenas de milisegundos en el
navegador. Desplazar la retícula media celda puede añadir una **fila o columna
entera**, que es la mejora de capacidad más barata que existe.

Nota: solo hace falta barrer θ en [0°, 180°) porque una retícula rectangular a
θ y a θ+180° es la misma.

---

## 4. Separación entre filas (criterio IDAE)

`layoutEngine.js:16` implementa:

```
d = h / tan(61° − |latitud|)      con h = L · sen(β)
```

donde `L` es el lado del módulo en la dirección de la pendiente. Es el criterio
del IDAE (Pliego de Condiciones Técnicas de Instalaciones Conectadas a Red):
garantiza **cero sombra durante 4 horas alrededor del mediodía solar en el
solsticio de invierno**. El `61° − |lat|` es la elevación solar de referencia
en ese instante.

Verificación: para β = 30°, L = 1,72 m y lat = 40,4°, sale h = 0,86 m y
d = 0,86 / tan(20,6°) = **2,29 m** de separación entre bordes de fila.

---

## 5. Sombra entre filas como pérdida, no como restricción

Hoy `d` es un mínimo inviolable. En la práctica profesional interesa poder
**apretar** (subir el *ground coverage ratio*): la sombra que aparece es de
invierno, cuando la producción es baja, y los módulos extra rinden todo el año.

### Cálculo

Para una separación `d' < d`, la altura de sombra proyectada sobre la fila
siguiente al instante de elevación α y azimut γ_s es:

```
sombra_proyectada = h / tan(α) · cos(γ_s − θ_filas)   [dirección normal a la fila]
fracción_tapada   = max(0, (sombra_proyectada − d') / L_proyectado)
```

Integrando la fracción tapada ponderada por la irradiación de cada instante a
lo largo del año se obtiene la **pérdida anual**. Se muestra al usuario junto a
la ganancia de capacidad:

> «Acercando las filas a 2,1 m caben 6 módulos más y pierdes un 2,3 % anual.»

### La regla de cableado que se deriva

**La sombra entre filas es uniforme a lo largo de toda la fila**: tapa la banda
inferior de la fila entera, no una esquina. Y un módulo sombreado arrastra a
todo su string.

> **Los strings deben cablearse a lo largo de las filas, no cruzándolas.**

Si un string sube en vertical atravesando las cinco filas, la sombra de
invierno afecta a **todos** los strings. Si cada string recorre su fila, la
sombra queda contenida en uno y los demás siguen a plena potencia. Misma
pérdida física, casi el doble de producción. Solo depende de cómo se agrupen
las celdas, así que es una restricción que el optimizador puede respetar gratis.

---

## 6. Sombra de obstáculos

### El datum: sin él, «altura» no significa nada

Un árbol de 8 m no sombrea un campo situado en un tejado a 6 m. Lo que importa
es la diferencia de cotas:

```
h_eficaz = (cota_base_obstáculo + altura_obstáculo) − cota_del_plano_del_campo
```

Si sale ≤ 0, el obstáculo se descarta sin más cálculo. La chimenea lleva
`cota_base` = cota del tejado; el árbol y el edificio vecino, `cota_base = 0`.

**Limitación asumida**: en un faldón inclinado la cota del campo no es
constante (el alero está más bajo que la cumbrera), así que la misma sombra
tapa más celdas abajo que arriba. La primera versión usa una cota de referencia
única. Hacerlo exacto exige saber qué borde del polígono es la cumbrera, dato
que hoy no se pide.

### Exclusión y obstáculo son cosas distintas

Hoy están fundidos en una sola entidad, y eso hace imposible modelar dos casos
reales:

| | Impide colocar | Proyecta sombra | Ejemplos |
|---|---|---|---|
| **Exclusión** | Sí | Casi nada (enrasada) | Lucernario, claraboya, registro |
| **Obstáculo** | No necesariamente | Sí | Chimenea, shunt, antena, peto, **árbol, edificio vecino** |

Un árbol vecino no excluye nada del tejado pero sombrea mucho; un lucernario
excluye pero no sombrea. Separarlos es requisito para que el cálculo tenga
sentido.

### Magnitud del efecto

La sombra de un obstáculo de altura eficaz `h` al mediodía del solsticio de
invierno mide `h / tan(α)`. Con α = 26,2° (Madrid):

```
longitud_sombra = h / tan(26,2°) = 2,03 · h
```

**Una chimenea de 1,2 m proyecta 2,4 m de sombra al norte**, que son dos filas
de módulos que hoy se colocan como si no existiera.

### Ventana solar, no instante

Una sola sombra de mediodía subestima. Se usa la misma ventana que el criterio
IDAE — **4 horas alrededor del mediodía solar del solsticio de invierno** — y
se calcula la **unión de sombras** en esa ventana:

```
para t en la ventana (paso 15 min):
    sol = sun_vector(lat, δ_invierno, ω(t))
    si sol.up <= 0: continuar
    desplazamiento = (−sol.este/sol.up · h,  −sol.norte/sol.up · h)
    sombra(t) = footprint_obstáculo trasladado por desplazamiento
```

Cada celda recibe una **puntuación de sombreado** ∈ [0, 1]: la fracción de la
ventana en la que está tapada, ponderada opcionalmente por la irradiación de
cada instante. No es un sí/no, así que el optimizador puede **preferir** la
celda menos sombreada en vez de descartar en binario.

### Transmitancia: el árbol no es opaco

Un caduco sin hoja transmite del orden de la mitad de la luz; en hoja, casi
nada. Modelarlo con `transmitancia` (o `tipo: opaco | caduco | perenne`)
convierte la sombra en una **penalización proporcional** en lugar de una
exclusión. Un edificio sí es opaco. Es la diferencia entre descartar media
cubierta y perder un 4 % anual.

---

## 7. Sistemas de anclaje: «anclable» es una consecuencia, no una propiedad

Pedir al usuario que dibuje a mano el área anclable en cada proyecto es
trasladarle un trabajo que el modelo puede inferir. Lo que determina las
restricciones es el **sistema de anclaje**:

| Sistema | Qué restringe | Retranqueo típico |
|---|---|---|
| Coplanar sobre teja (ganchos) | Los ganchos caen en **correas/cabios**: hay retícula estructural debajo y los raíles van perpendiculares a ella | Bajo |
| Coplanar sobre chapa / sándwich | Grapa en el grecado: el **paso del grecado** fija dónde van los raíles | Bajo |
| Cubierta plana lastrada | No perfora, pero limita la **carga admisible (kg/m²)**; el perímetro concentra succión de viento | **Alto (1–1,5 m)** |
| Cubierta plana anclada mecánicamente | Perfora la impermeabilización: debe caer en elemento estructural; la garantía de la membrana puede vetar zonas | Medio |
| Estructura en suelo / marquesina | Otro dominio | — |

El sistema aporta por defecto: **(a)** el retranqueo de borde, **(b)** si hay
retícula estructural que condicione la rotación, **(c)** si hay límite de carga
que limite la densidad.

Consecuencia sobre la rotación: **en teja la rotación deja de ser libre.** Los
raíles quieren ir perpendiculares a los cabios, así que el optimizador debe
**penalizar** las rotaciones incompatibles con la retícula estructural en lugar
de elegir simplemente la que más empaqueta.

El **polígono anclable manual queda como vía de escape** para lo que el modelo
no puede inferir («este faldón tiene el forjado dañado»), no como mecanismo
principal.

### Retranqueo: implementación

El retranqueo se aplica erosionando el polígono útil, no filtrando celdas una a
una: `polígono_útil = erosionar(roof ∩ anchorable, setback_m)`. Para polígonos
convexos o casi convexos basta desplazar cada arista hacia dentro; para
cóncavos conviene el *offset* por Minkowski. Alternativa suficiente y mucho más
simple: exigir que **la distancia de cada esquina de la celda al borde del
polígono** sea ≥ setback.

---

## 8. Función objetivo: dos regímenes

Hoy, cuando caben más celdas que las requeridas, `PanelLayout.jsx:234-238`
ordena por distancia al centroide del conjunto que encaja. Eso produce un
**blob redondeado**, que no optimiza ni capacidad ni producción ni coste de
montaje.

**Si capacidad ≥ N requeridos**, la capacidad extra no vale nada. El objetivo
es colocar exactamente N en el mejor sitio:

```
maximizar   Σ (1 − sombreado_celda) · peso_irradiación
sujeto a    compacidad (filas completas, bloque contiguo)
            homogeneidad de sombra dentro de cada string
            divisibilidad entre entradas MPPT
```

La compacidad no es estética: menos raíl, menos tirada de cable, mejor acabado
y menos puntos de fijación. Se puede expresar como minimizar el perímetro del
conjunto seleccionado, o preferir filas completas antes que filas parciales.

**Si capacidad < N**, manda la capacidad, y el déficit dispara el flujo de la
sección 10.

---

## 9. Multi-zona

El requisito «el instalador querrá **agregar** área» convierte el multi-zona en
inevitable: una segunda zona es un polígono con **su propio azimut,
inclinación y sistema de anclaje**. Retrofitearlo después sería peor que
hacerlo ahora.

Cada zona tiene su retícula independiente y su propia optimización; la
producción total es la suma por zona (cada una con su β y γ), lo cual además
mejora el cálculo: hoy un tejado a dos aguas se modela con un solo azimut, que
es incorrecto.

---

## 10. Flujo cuando el área es insuficiente

Hoy es un `toast` de aviso (`PanelLayout.jsx:244`). Debe ser una **pantalla de
decisión con las consecuencias cuantificadas**:

| Opción | Qué hay que mostrar |
|---|---|
| Añadir otra zona | Su azimut e inclinación propios → producción distinta |
| Módulo de más potencia | **Recalcula cuántos hacen falta**: menos módulos, más grandes |
| Apretar las filas | «+6 módulos, −2,3 % anual» (sección 5) |
| Girar a paisaje | Cuántos caben con cada rotación |
| Aceptar menos potencia | Recalcular el caso financiero con la nueva producción |

**Punto de integración**: cambiar el modelo de panel vuelve atrás al paso de
análisis, porque `requiredPanels` sale de allí. Hay que cerrar ese bucle o el
usuario acabará con un layout que no corresponde a su cálculo.

---

## 11. Modelo de datos

Encaja en el `layout` JSON que ya se persiste en `Project._layout`, sin
migración de esquema:

```
layout = {
  zones: [{
    id, name,
    roof:        [[lat,lng], ...],
    anchorable:  [[lat,lng], ...] | null,
    plane:       { azimut, tilt, coplanar, elevation_m },
    anchor:      { system, setback_m, load_limit_kg_m2?,
                   structural: { azimut, pitch_m }? },
    rows:        { rotation, orientation: 'v'|'h', gap_m, phase: [dx, dy] },
    cells:       [[i,j], ...],
    strings:     [[cellKey, ...], ...],
    origin:      [lat,lng],
  }],
  exclusions: [{ zone_id?, poly }],
  obstacles:  [{ poly, height_m, base_elevation_m, transmittance }],
  optimizer:  { objective, shading_window_h, score, computed_at },
}
```

**Compatibilidad**: el formato actual (`roof`, `exclusions`, `cells`,
`orientation`, `origin`, `azimut`, `rowGap`) se lee y se migra a una zona única
al cargar. Los `exclusions` actuales son arrays de puntos; el lector acepta
ambas formas.

---

## 12. Plan de implementación

### `frontend/src/features/design/layoutEngine.js`

| Función | Estado |
|---|---|
| `localConverter`, `pointInPolygon`, `polygonAreaM2`, `centroid` | Sin cambios |
| `idaeRowGap` | Sin cambios; se añade `interRowShadingLoss(gap, ...)` |
| `makeGrid` | Acepta `rotation` y `phase` explícitos, desacoplados del azimut del módulo |
| `cellFits` | Añade retranqueo y polígono anclable |
| `autoLayoutCells` | Pasa a devolver capacidad; la selección se separa |
| **`sunVectorAt(lat, decl, ω)`** | Nueva: puerto mínimo de `solar_geometry.py` |
| **`obstacleShadingScore(cell, obstacles, lat, plane)`** | Nueva |
| **`optimizeLayout(zone, obstacles, required)`** | Nueva: barrido θ × orientación × fase |
| **`selectBest(candidates, required, scores)`** | Nueva: compacidad + sombra + strings |
| **`assignStrings(cells, mpptInputs)`** | Nueva: agrupa a lo largo de filas |

### `frontend/src/features/design/PanelLayout.jsx`

- Selector de rotación libre en pasos de 5° con el coste de irradiación cuando
  no es coplanar.
- **Medición por tres clicks**: clicks 1-2 trazan una línea de referencia real
  del mapa (cumbrera, alero, peto) y el 3 indica hacia qué lado miran las
  filas. Se calcula el rumbo absoluto de la línea desde las coordenadas y se
  convierte a azimut absoluto redondeado a 5°. El usuario piensa en la
  geometría del edificio, no en grados de brújula: nadie acierta 217° a ojo,
  pero todo el mundo clica bien un alero. Al soltar el tercer click se ofrecen
  **las dos opciones ortogonales** (paralela y perpendicular) con la capacidad
  de cada una.
- Alta de obstáculos con `height_m`, `base_elevation_m` y tipo.
- Selector de sistema de anclaje que rellena el retranqueo por defecto.
- Gestión de zonas (añadir, renombrar, borrar).
- Pantalla de déficit de la sección 10.

### Servidor

`site_plan_service.py` debe pintar todas las zonas, los obstáculos con su
sombra y el retranqueo, para que el plano del documento refleje lo mismo que la
pantalla.

---

## 13. Verificación prevista

- **Astronomía**: ya validada en `solar_geometry.py` (Madrid 73,0° verano /
  26,2° invierno, equinoccio 90,0° de azimut y 12,0 h).
- **Fase**: comprobar que la capacidad óptima ≥ la capacidad con fase 0 en un
  conjunto de polígonos de prueba (invariante que debe cumplirse siempre).
- **Sombra**: caso analítico con un obstáculo rectangular y sol a 45° — la
  sombra debe medir exactamente `h`.
- **Retranqueo**: ninguna celda seleccionada a menos de `setback` del borde.
- **Strings**: cada string contiguo y con puntuación de sombreado homogénea.

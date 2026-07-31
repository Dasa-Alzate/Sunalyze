# Dimensionado eléctrico y protecciones — teoría, cálculos e implementación

Documento de **2026-07-29**. Cubre el dimensionado de strings, los límites del
inversor y los criterios de protección, con el plan de implementación.

> ⚠️ **Aviso de fiabilidad y alcance de las citas.** Las fuentes de la
> bibliografía se citan **por su identificador y título**, que son verificables.
> Lo que **no** se ha verificado contra el texto articulado es la atribución
> exacta de cada umbral numérico al artículo concreto que lo fija: los valores
> están redactados desde conocimiento general del dominio y señalan la norma
> donde deben confirmarse. **Ningún umbral de este documento debe convertirse en
> cálculo automático ni en texto de la memoria sin contrastarlo con el texto
> oficial.** Lo marcado como *estado del código* sí está verificado sobre el
> repositorio.

---

## 1. Qué cambió en quince años

La observación de partida es correcta: el cálculo no desapareció, **cambió de
sitio**.

**Antes.** MPPT o regulador como aparato independiente, muy a menudo acoplado a
baterías. Dimensionabas el campo contra el banco, ponías fusibles por rama, y
las protecciones de máxima/mínima tensión y frecuencia eran relés que montabas
tú.

**Ahora.** Inversor de string sin transformador con 2–N MPPT integrados,
seccionador DC incorporado, vigilancia de aislamiento (Riso) y de corriente
residual (RCMU) dentro del aparato, y protecciones de red certificadas de fábrica
conforme a UNE-EN 62109-2 [6]. Lo que queda en manos del proyectista:

1. **Demostrar que el campo respeta los límites del inversor en todo el rango de
   temperatura.** Es el cálculo central y el que destruye equipos si falta.
2. **Dimensionar el cable** para que soporte la corriente de forma permanente
   [3][4].
3. **Proveer aislamiento** para mantenimiento y protección frente a corriente
   inversa y sobretensiones [3][4][10].
4. **Justificar en la memoria** qué protecciones aporta el inversor y cuáles se
   añaden, con su certificación [6][7].

---

## 2. El cambio conceptual: en DC no se protege por sobrecorriente

Es lo que más confunde a quien viene de instalaciones convencionales.

> **Un campo fotovoltaico es una fuente limitada en corriente.** Su corriente de
> cortocircuito (Isc) apenas supera la de trabajo (Impp) —relación típica
> Isc/Impp ≈ 1,06—, de modo que **un fusible no puede despejar una falta por
> sobrecorriente en un campo FV**: no existe la sobrecorriente que lo haría
> fundir. Este principio es el que gobierna el diseño de protecciones en
> IEC 62548 [3] y en UNE-HD 60364-7-712 [4].

Consecuencias prácticas:

- El cable DC **no se protege con un dispositivo que salte**; se dimensiona para
  que su intensidad admisible sea ≥ 1,25 · Isc de forma permanente. El factor
  1,25 cubre el refuerzo de irradiancia (reflexiones, nubes brillantes) y el
  coeficiente de temperatura de Isc [3]. ITC-BT-40 [1e] exige asimismo
  dimensionar la línea de generación para el 125 % de la corriente máxima.
- Los dispositivos DC existen para **aislar** en mantenimiento (seccionador),
  **impedir corriente inversa** hacia una rama en falta (fusibles de rama) y
  **derivar sobretensiones** (SPD) [3][4][1d].
- Una falta a tierra o un arco no se detectan por corriente: los detecta el
  **inversor** por vigilancia de aislamiento y, cada vez más, detección de arco
  [6].

Corolario para la memoria: el texto **no** debe decir «el magnetotérmico protege
el tramo DC», porque es falso. Debe justificar la intensidad admisible del cable
y el elemento de corte.

---

## 3. Ventana de tensión: el cálculo central

### 3.1 Límite superior — Voc a temperatura mínima

Con frío la tensión sube. El caso peor es el amanecer de un día invernal a
circuito abierto:

```
Voc_string(T_min) = N_serie · Voc_STC · [1 + (β_Voc/100) · (T_min − 25)]
```

con `β_Voc` en %/°C y **negativo**, tomado de la ficha del módulo caracterizada
según IEC 61215 [8]. La condición, recogida en IEC 62548 [3]:

```
Voc_string(T_min) · margen  <  V_dc_max del inversor
N_max = piso[ V_dc_max / (Voc_STC · [1 + (β_Voc/100)·(T_min − 25)] · margen) ]
```

**Estado del código: implementado y verificado.** `analysis_service.py:146-150`
calcula `max_cell_amount` y `vmax_coldest_day`; la línea 160 aplica margen 1,05;
`_find_compatible_inverters` (línea 283) lo usa para filtrar inversores. Es el
cálculo que evita destruir el inversor y está bien planteado.

**T_min** debe ser la mínima histórica extrema del emplazamiento, no la media del
mes más frío [3]. El interior de la península baja de −5 °C con holgura y hay
zonas que alcanzan −12 °C; en costa mediterránea rara vez baja de 0 °C. Conviene
documentar el origen del `coldest_temp` que usa hoy el servicio.

### 3.2 Límite inferior — Vmpp a temperatura de célula alta

**Este es el hueco.** Con calor la tensión baja, y si la Vmpp del string cae por
debajo de la tensión mínima de seguimiento del MPPT, **el inversor se sale de
rango**.

Temperatura de célula por el modelo NOCT, con la NOCT definida y medida según
IEC 61215 [8] y la expresión de uso estándar recogida en la literatura de
referencia [2]:

```
T_célula = T_ambiente + (NOCT − 20)/800 · G
```

Con NOCT = 45 °C y G = 1000 W/m²: `T_célula = T_amb + 31,25`. Con 40 °C de
ambiente da **71 °C de célula**, de donde sale la cifra de referencia de ~70 °C.

```
Vmpp_string(T_alta) = N_serie · Vmp_STC · [1 + (β_Vmp/100) · (T_célula − 25)]

condición:  Vmpp_string(T_alta) > V_mppt_min del inversor
N_min = techo[ V_mppt_min / (Vmp_STC · [1 + (β_Vmp/100)·(T_célula − 25)]) ]
```

**Estado del código: no existe.** Verificado: no hay `mppt_v_min`, ni temperatura
de célula caliente, ni comprobación de Vmpp en `analysis_service.py` ni en el
modelo `Inverter`, que solo guarda `vmax`.

**Consecuencia práctica**, fea y difícil de diagnosticar: strings demasiado
cortos entran en rango en invierno y **se caen del MPPT a mediodía en agosto**,
justo con la máxima irradiación. El cliente reporta «se apaga a las dos de la
tarde» y no hay nada en el expediente que lo explique.

**Trampa de datos:** guardamos `tcv` (coeficiente de Voc) pero **no el de Vmp**.
β_Vmp es **más negativo** que β_Voc —típicamente −0,40 %/°C frente a
−0,28 %/°C—, de modo que usar β_Voc para estimar la Vmpp caliente
**sobreestima** la tensión y es **no conservador** justo en el lado donde el
error duele. Mientras no tengamos β_Vmp hay que aplicar margen explícito y
declarar que es estimación.

### 3.3 El resultado que interesa al usuario

De 3.1 y 3.2 sale el **rango admisible de módulos en serie** `[N_min, N_max]`,
que es la información que un instalador quiere ver:

> Con este panel y este inversor puedes poner **entre 8 y 14 módulos en serie**.
> Con 18 módulos en 2 ramas de 9, estás dentro.

---

## 4. Límites de corriente por MPPT

```
Isc_diseño   = Isc_STC · 1,25 · N_paralelo   ≤  Isc_max admisible por MPPT
Impp_diseño  = Impp_STC · N_paralelo          ≤  I_entrada_max por MPPT
```

El 1,25 es el mismo factor de la sección 2 [3]. Son **dos límites distintos**:
uno de cortocircuito (soportabilidad) y otro de operación (capacidad de
seguimiento). Un inversor puede admitir 22 A de operación y 41 A de
cortocircuito por MPPT — cifras reales leídas en las fichas de Fronius durante
la extracción del catálogo.

---

## 5. Ratio DC/AC (sobredimensionado)

```
ratio = potencia_pico_DC / potencia_nominal_AC
```

La práctica moderna sobredimensiona deliberadamente (1,1–1,3): el recorte de
picos es pequeño en energía anual y el inversor es la parte cara. Dos límites:

- El fabricante indica una potencia DC máxima recomendada [6].
- En España la **potencia del inversor** fija la categoría administrativa del
  expediente y los requisitos de tramitación [7][9], así que el ratio tiene
  lectura regulatoria además de técnica.

---

## 6. Protecciones DC

### 6.1 Fusibles de rama

El criterio real no es «a partir de N ramas», sino: **¿puede la corriente inversa
que inyectan las demás ramas en una rama en falta superar lo que el módulo
admite?** El dato que lo decide es el **calibre máximo de fusible en serie** de
la ficha, parámetro definido en la cualificación del módulo [8][11].

Regla de oficio: con **2 ramas por MPPT** normalmente no hacen falta, porque una
rama soporta la inversa de la otra; **a partir de 3** sí. *(Contrastar con
IEC 62548 [3] antes de automatizar.)*

**Dato que falta:** `panel.max_series_fuse_a`. Sin él no se puede dimensionar.

### 6.2 Seccionador DC

Obligatorio para aislar en mantenimiento [3][4]. Calibre ≥ 1,25 · Isc y tensión
asignada ≥ Voc a T_min. **Habitualmente integrado** en el inversor moderno, de
modo que lo normal es no añadir uno — pero la memoria debe justificar que existe
y dónde.

### 6.3 Protección contra sobretensiones (SPD)

Tipo 2 en el lado DC cuando la tirada de cable supera cierta longitud (se maneja
un umbral del orden de 10 m) o el emplazamiento está expuesto a rayo.
Referencia: ITC-BT-23 [1d]. Hay campos `protections_dc_*` en la memoria, así que
la estructura ya existe.

### 6.4 Campo flotante — trampa de la escuela antigua

Los inversores **sin transformador exigen que ningún polo del campo esté puesto
a tierra**. Poner a tierra un polo, práctica válida con inversores con
transformador, **destruye el aparato moderno** y dispara la vigilancia de
aislamiento [4][6]. Merece ser comprobación explícita del validador, no una nota
al pie.

---

## 7. Protecciones AC

| Elemento | Criterio | Fuente | Nota «antes/ahora» |
|---|---|---|---|
| Magnetotérmico | ≥ 1,25 · I_max_salida, coordinado con el cable | [1e][1b] | Sin cambios |
| **Diferencial** | 30 mA, **tipo A o B** | [4][6] | Un tipo AC **no vale** con inversor sin transformador: la fuga puede tener componente continua que lo ciega. Muchos inversores integran RCMU, lo que cambia qué hace falta fuera |
| Máx/mín tensión y frecuencia, antiisla | Lo aporta el **inversor certificado** | [6][7] | Antes eran relés que montabas. Hoy la memoria cita la certificación del equipo, no describe relés |
| Inyección cero | Cuando no hay registro para excedentes | [9] | Campo `zero_inyection_model` ya existe |

**No importar del NEC:** el *rapid shutdown* que aparece en documentación
anglosajona es requisito estadounidense (NEC 690.12 [12]), **no español**. No
debe figurar en nuestras memorias.

---

## 8. Puesta a tierra

- ITC-BT-18 [1c]: equipotencialidad de marcos y raíles, y límites de resistencia
  de puesta a tierra.
- La **puesta a tierra funcional** del campo no se hace (§6.4); se ponen a tierra
  las **masas** (estructura, marcos), no los polos activos [4].
- El aislamiento (Riso) lo verifica el inversor en cada arranque [6].

---

## 9. Caída de tensión

- **Tramo DC**: el pliego del IDAE [5] recomienda mantenerla baja (del orden del
  1,5 %), porque es pérdida pura de energía.
- **Tramo AC de la línea de generación**: límite fijado en ITC-BT-40 [1e].
  *(Verificar el porcentaje exacto en el texto de la instrucción antes de
  automatizarlo.)*

La memoria ya menciona la caída de tensión (`memoria_tecnica_pdf.html:569`), y la
tabla de intensidades admisibles que cita procede de UNE-HD 60364-5-52 [1f].

---

## 10. Datos que faltan y de dónde salen

Cuatro campos en `Inverter` y uno en `Panel`. Lo relevante es que **el dato ya
está en las fuentes conectadas y hoy se descarta**:

| Campo | Para qué | Dónde está |
|---|---|---|
| `mppt_v_min` | Límite inferior de la ventana (§3.2) | Fronius ES publica `Rango de tensión MPP (Umpp mín. - Umpp máx.)`; CSV del CEC [13]: `Mppt_low` |
| `mppt_v_max` | Ventana de seguimiento | Ídem; CEC `Mppt_high` |
| `mppt_count` | Reparto en ramas y strings | Fronius ES: `Número de MPPT` |
| `isc_max_per_mppt` | Límite de cortocircuito (§4) | Fronius ES: `Máxima corriente de cortocircuito`; CEC `Idcmax` |
| `panel.max_series_fuse_a` | Fusibles de rama (§6.1) | Ficha del fabricante [8][11]; **no** está en el CSV del CEC |

`fronius.py:96` usa hoy `Tensión MPP máxima` **solo como respaldo de `vmax`** y
**descarta el mínimo**. Es cambio de pocas líneas.

---

## 11. Plan de implementación

### 11.1 Modelo y migración

Añadir a `Inverter`: `mppt_v_min`, `mppt_v_max`, `mppt_count`,
`isc_max_per_mppt`. Añadir a `Panel`: `max_series_fuse_a`. Todos **nullable**,
por el principio de degradación gradual: la ausencia de un campo reduce el nivel
de detalle alcanzable, no bloquea el flujo.

### 11.2 Extracción

- `fronius.py`: capturar el rango MPP completo, el número de MPPT y la corriente
  de cortocircuito admisible, en lugar de usar el máximo solo como respaldo.
- `cec.py`: valorar importar los inversores CEC **solo** para los campos de la
  ventana DC, que son propiedad del hardware y no de la variante de red; el lado
  AC (208/240 V) seguiría descartado.

### 11.3 `app/services/string_sizing_service.py` (nuevo)

```
StringSizingService.evaluate(panel, inverter, site) -> {
  series_range:   { min, max, computed_with },
  configurations: [{ n_series, n_parallel, voc_cold, vmpp_hot, isc_design, verdict }],
  checks:         [{ id, label, value, limit, verdict, source, note }],
  detail_level:   'completo' | 'parcial' | 'no_disponible',
  missing:        [{ field, entity, unlocks }],
}
```

Cada `check` con veredicto `ok | aviso | fallo`, el número que lo respalda y **la
referencia normativa**, de modo que el resultado sirva tanto a la UI como al
texto justificativo de la memoria. `missing` alimenta la tarjeta de degradación.

Comprobaciones: Voc frío vs V_dc_max · Vmpp caliente vs V_mppt_min · Isc diseño
vs Isc admisible · Impp vs I entrada · ratio DC/AC · necesidad de fusible de rama
· campo flotante · caída de tensión DC y AC.

### 11.4 Integración

- **Paso de diseño**: mostrar `[N_min, N_max]` y validar la configuración en
  vivo.
- **Disposición**: `assignStrings` respeta `mppt_count` y la regla de cablear a
  lo largo de las filas (`docs/disposicion-teoria-e-implementacion.md` §5).
- **Memoria**: los `checks` alimentan el texto justificativo con su cita.

---

## 12. Por qué esto era el hueco correcto

`documentation/analisis-competencia-v2.md` marca **«string sizing con
temperaturas extremas» como prioridad Alta y ROI-2**, con la nota de empezar por
ahí.

Lo que no estaba dicho es que **el trabajo de catálogo era su condición previa**:
el dimensionado no se puede hacer sin la ventana MPP y el número de MPPT del
inversor, y esos campos solo existen si alguien los extrae de la ficha del
fabricante. El catálogo multifuente no era un fin en sí mismo, era el cimiento
del hueco de ingeniería que más nos separa de los vecinos comerciales.

---

## Bibliografía

**Reglamentación española**

[1] **Real Decreto 842/2002**, de 2 de agosto, por el que se aprueba el
Reglamento Electrotécnico para Baja Tensión (REBT). BOE núm. 224, 18-09-2002.
Instrucciones Técnicas Complementarias citadas:
 [1b] **ITC-BT-19** — Instalaciones interiores o receptoras. Prescripciones
 generales (intensidades admisibles).
 [1c] **ITC-BT-18** — Instalaciones de puesta a tierra.
 [1d] **ITC-BT-23** — Protección contra sobretensiones.
 [1e] **ITC-BT-40** — Instalaciones generadoras de baja tensión.
 [1f] **UNE-HD 60364-5-52** — Instalaciones eléctricas de baja tensión. Parte
 5-52: Selección e instalación de equipos eléctricos. Canalizaciones. (Origen de
 la tabla de intensidades admisibles C.52-1 bis.)
 [1g] **ITC-BT-21** — Tubos y canales protectores.

[7] **Real Decreto 1699/2011**, de 18 de noviembre, por el que se regula la
conexión a red de instalaciones de producción de energía eléctrica de pequeña
potencia.

[9] **Real Decreto 244/2019**, de 5 de abril, por el que se regulan las
condiciones administrativas, técnicas y económicas del autoconsumo de energía
eléctrica.

**Normas técnicas**

[3] **IEC 62548** / UNE-EN IEC 62548 — *Photovoltaic (PV) arrays — Design
requirements.* Norma de referencia para dimensionado de campo, factores de
seguridad de corriente, fusibles de rama y seccionamiento.

[4] **UNE-HD 60364-7-712** — *Instalaciones eléctricas de baja tensión. Parte
7-712: Requisitos para instalaciones o emplazamientos especiales. Sistemas de
alimentación fotovoltaica solar (PV).*

[6] **UNE-EN 62109-1** y **UNE-EN 62109-2** — *Seguridad de los convertidores de
potencia utilizados en sistemas fotovoltaicos.* Parte 2: requisitos particulares
para inversores.

[8] **IEC 61215** — *Terrestrial photovoltaic (PV) modules — Design
qualification and type approval.* Define las condiciones STC y NOCT y los
coeficientes de temperatura publicados en ficha.

[11] **IEC 61730** — *Photovoltaic (PV) module safety qualification.* Origen del
calibre máximo de fusible en serie declarado en la ficha del módulo.

[12] **NFPA 70 — National Electrical Code**, art. 690.12 (*Rapid Shutdown of PV
Systems on Buildings*). **Requisito estadounidense, citado únicamente para
descartarlo del ámbito español.**

**Documentación técnica y de referencia**

[5] **IDAE** — *Pliego de Condiciones Técnicas de Instalaciones Conectadas a
Red* (PCT-C, rev. julio 2011). Instituto para la Diversificación y Ahorro de la
Energía. Origen del criterio de separación entre filas
`d = h / tan(61° − |latitud|)` y de las recomendaciones de caída de tensión.

[2] **Duffie, J. A.; Beckman, W. A.** — *Solar Engineering of Thermal
Processes*, 4.ª ed., Wiley, 2013. Referencia canónica para geometría solar
(declinación, ángulo horario, ángulo de incidencia) y para el modelo de
temperatura de célula basado en NOCT.

[10] **Comisión Electrotécnica Internacional** — serie **IEC 62305**
(*Protection against lightning*), como marco de la selección de SPD referida en
ITC-BT-23.

[13] **NREL** — *System Advisor Model (SAM), librerías de componentes*:
`CEC Modules.csv` y `CEC Inverters.csv`, distribución de las listas de equipos
homologados de la **California Energy Commission**.
<https://github.com/NREL/SAM> · Portal CEC:
<https://solarequipment.energy.ca.gov/>

---

### Nota sobre el uso de estas fuentes

Las referencias identifican **dónde** está regulado cada criterio, no sustituyen
su lectura. Para cualquier valor que vaya a automatizarse o a imprimirse en una
memoria firmada, el flujo correcto es: localizar el artículo o tabla concreta en
el texto oficial vigente, transcribir el valor, y registrar la referencia exacta
(artículo y edición) en el `check` correspondiente del `StringSizingService`, de
modo que el documento generado pueda citarla.

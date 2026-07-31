# Niveles de detalle y degradación gradual

Documento de **2026-07-29**. Define cómo el sistema debe comportarse cuando falta
información: qué exige cada paso, qué es opcional, qué nivel de detalle se
alcanza con cada conjunto de datos, y cómo se comunica al usuario.

**Principio rector:** *ningún paso del flujo se bloquea por un dato que no
necesita.* Un dato ausente reduce el **nivel de detalle alcanzable** y se
comunica; no interrumpe el trabajo del usuario.

---

## 1. El problema, medido

Con el catálogo multifuente el número de equipos pasó de 163 paneles a 3.674, y
con él la variedad de completitud. Estado real del catálogo hoy:

| Entidad | Campo | Sin valor | Origen del hueco |
|---|---|---|---|
| Panel (3.674) | `tcv`, `tcp`, `t_noct` | **152** | AutoSolar no publica coeficientes de temperatura |
| Panel | `height`, `width` | **3.592** | El CSV del CEC solo trae dimensiones en el 26 % de las filas |
| Panel | `y` | 11 | — |
| Inversor (207) | `I_max_input`, `I_max_output` | **121** | Fichas que no publican corrientes |
| Inversor | `y` | 55 | — |
| Batería (376) | `voltage` | 353 | La Battery List del CEC no publica tensión nominal |

### El fallo que esto ya provoca

`analysis_service.py:150` hace aritmética directa sobre un campo **nullable**:

```python
vmax_coldest_day = panel.voc * (1 + (-1 * panel.tcv * (25 - coldest_temp) / 100))
```

Verificado ejecutando el cálculo con un panel real del catálogo:

```
panel sin tcv: Panel Solar 500W Tensite Full Black TOPCon N | voc=44.4 tcv=None
REVIENTA -> TypeError: unsupported operand type(s) for *: 'int' and 'NoneType'
```

**152 de los 3.674 paneles del catálogo hacen caer el paso de análisis** si el
usuario los elige. No degradan: rompen.

### El fallo silencioso, que es peor

`crud.py` define para la creación manual de paneles:

```python
'defaults': {'y': 0, 'tcp': 0, 'tcv': 0, 'isc': 0, 't_noct': 45, ...}
```

Un `tcv = 0` no revienta: hace que `vmax_coldest_day = Voc_STC`, es decir,
**desactiva silenciosamente la corrección de tensión por frío**. Verificado:

```
con tcv=0 → vmax_coldest_day = 45.0 = Voc STC
```

Eso es **no conservador en el lado que importa**: subestima la tensión de
circuito abierto en un día frío, que es justo el cálculo que impide superar la
`V_dc_max` del inversor y destruirlo
(`docs/dimensionado-electrico-string-sizing.md` §3.1). Un cero por defecto en un
coeficiente físico es peor que un nulo, porque el nulo se puede detectar y el
cero se confunde con un dato medido.

**Regla que se deriva:** los valores por defecto solo son aceptables cuando el
valor neutro es *físicamente cierto*. Para coeficientes de temperatura,
dimensiones o corrientes, el defecto correcto es **NULL**, y el consumidor debe
tratarlo.

---

## 2. Niveles de detalle

Cada capacidad del sistema declara los niveles que puede alcanzar y qué datos
necesita cada uno. Los niveles son acumulativos.

### 2.1 Dimensionado y producción

| Nivel | Qué entrega | Requiere |
|---|---|---|
| **L0 — estimación** | Producción anual aproximada por potencia pico e irradiación de PVGIS | `panel.power`, ubicación |
| **L1 — eléctrico básico** | Número de módulos en serie máximo y compatibilidad con el inversor | + `panel.voc`, `panel.tcv`, `inverter.vmax`, T_min |
| **L2 — ventana completa** | Rango admisible `[N_min, N_max]`, aviso de caída del MPPT en verano | + `panel.vmp`, `panel.t_noct`, `inverter.mppt_v_min` |
| **L3 — corrientes y protecciones** | Verificación de límites por MPPT y criterio de fusibles de rama | + `panel.isc`, `panel.max_series_fuse_a`, `inverter.isc_max_per_mppt`, `inverter.mppt_count` |

### 2.2 Disposición

| Nivel | Qué entrega | Requiere |
|---|---|---|
| **L0 — área** | Cuántos módulos caben por superficie | `panel.power`, polígono |
| **L1 — retícula real** | Colocación alineada con paso y hueco entre filas correctos | + `panel.height`, `panel.width` |
| **L2 — óptimo geométrico** | Rotación y fase optimizadas, retranqueo por sistema de anclaje | + sistema de anclaje |
| **L3 — sombras** | Puntuación de sombreado por celda y strings homogéneos | + obstáculos con altura y cota base |

Nota: **L1 es hoy inalcanzable para 3.592 de 3.674 paneles** por falta de
dimensiones. Es el hueco de datos más extendido del catálogo y el de mayor
impacto en la disposición.

### 2.3 Documento

| Nivel | Qué entrega | Requiere |
|---|---|---|
| **L0 — memoria básica** | Estructura y datos administrativos | Proyecto, cliente, ubicación |
| **L1 — justificación eléctrica** | Cálculos de tensión y corriente con su cita normativa | Nivel L1+ del dimensionado |
| **L2 — planos y tablas** | Plano de disposición, unifilares, tablas normativas | + disposición L1+, tablas cargadas |
| **L3 — fichas técnicas** | Fichas propias de cada equipo con curva I-V | + `voc`, `vmp`, `imp`, `isc` del panel |

### 2.4 Financiero

| Nivel | Qué entrega | Requiere |
|---|---|---|
| **L0 — ahorro estimado** | Comparativa de factura y ahorro anual | Producción, tarifa, consumo |
| **L1 — retorno** | VAN, TIR, payback | + CAPEX |
| **L2 — con ayudas** | Subvenciones por CCAA y deducciones | + CCAA y municipio |

---

## 3. Contrato de servicios: obligatorio frente a opcional

Todo servicio que consuma datos de equipo debe exponer su contrato de forma
explícita, en lugar de acceder a atributos y confiar en que existan.

```python
class CapabilityResult:
    value          # el resultado, o None si no se alcanzó ningún nivel
    level          # 'L0' | 'L1' | ...
    max_level      # el nivel que se habría alcanzado con datos completos
    missing        # [{ entity, field, label, unlocks, edit_url }]
    assumptions    # [{ field, used, reason }]  ← valores supuestos, declarados
```

Reglas:

1. **Nunca aritmética directa sobre un campo nullable.** Se resuelve con un
   accesor que devuelve `(valor, presente)` o que registra la ausencia.
2. **Si se supone un valor, se declara** en `assumptions` y viaja hasta el
   documento. Un supuesto no declarado es un dato inventado.
3. **El nivel alcanzado se propaga**: si el dimensionado queda en L1, la memoria
   no puede prometer justificación L2.
4. **Los `missing` llevan el enlace de edición** del equipo y el campo concreto,
   para que la tarjeta de la sección 4 sea accionable.

### Ejemplo aplicado al hueco real

```python
tcv, has_tcv = field_of(panel, 'tcv')
if has_tcv:
    voc_cold = panel.voc * (1 + tcv / 100 * (t_min - 25))
    level = 'L1'
else:
    voc_cold = panel.voc          # sin corrección
    level = 'L0'
    missing.append({
        'entity': 'panel', 'field': 'tcv',
        'label': 'Coeficiente de temperatura de Voc',
        'unlocks': 'Número máximo de módulos en serie y verificación de la '
                   'tensión máxima del inversor',
        'edit_url': f'/app/equipos?panel={panel.id}#tcv',
    })
    assumptions.append({
        'field': 'tcv', 'used': None,
        'reason': 'Sin coeficiente de temperatura no se corrige la Voc por frío; '
                  'el valor mostrado es el de STC y NO debe usarse para '
                  'verificar la tensión máxima del inversor.',
    })
```

Nótese que **no se sustituye por 0**: se declara que no hay corrección y se
advierte de que el número no sirve para lo que serviría el corregido.

---

## 4. La tarjeta de degradación

Donde un paso baje de nivel, aparece una tarjeta con tres elementos
obligatorios: **qué falta**, **qué se desbloquearía**, y **dónde añadirlo**.

```
┌──────────────────────────────────────────────────────────────┐
│ ⓘ  Cálculo con detalle reducido                              │
│                                                              │
│ Falta el coeficiente de temperatura de Voc (β) del panel     │
│ «Panel Solar 500W Tensite Full Black TOPCon N».              │
│                                                              │
│ Con ese dato podríamos calcular el número máximo de módulos  │
│ en serie y verificar que no se supera la tensión máxima del  │
│ inversor en un día frío.                                     │
│                                                              │
│ Ahora mismo la tensión mostrada es la de STC, sin corregir.  │
│                                                              │
│                                  [ Añadir el dato → ]        │
└──────────────────────────────────────────────────────────────┘
```

Criterios de diseño:

- **Informativa, no de error.** Tono neutro; el usuario no ha hecho nada mal.
- **Un dato por tarjeta** cuando son pocos; agrupada por equipo cuando son
  varios del mismo.
- **Enlace profundo** al campo concreto (`edit_url`), no a la pantalla genérica.
- **No se puede descartar de forma permanente** si afecta a un cálculo de
  seguridad (tensión máxima, corrientes): se puede plegar, no silenciar.
- **Aparece también en el documento**, en el apartado afectado, como nota de
  alcance. Lo que la pantalla advierte, el PDF lo advierte.

---

## 5. Auditoría por paso y por servicio

Lo que hay que revisar, con lo verificado hasta ahora.

### `analysis_service.py`

Accesos a campos nullable sin guarda, con su frecuencia:

| Campo | Accesos | Nullable | Sin valor en catálogo |
|---|---|---|---|
| `panel.tcv` | 4 | sí | 152 |
| `panel.tcp` | 2 | sí | 152 |
| `panel.t_noct` | 2 | sí | 152 |
| `panel.y` | 2 | sí | 11 |
| `panel.isc` | 2 | sí | 1 |
| `panel.height` / `width` | 3 / 3 | sí | 3.592 |
| `inverter.y` | 4 | sí | 55 |
| `inverter.I_max_output` | 1 | sí | 121 |
| `inverter.I_max_input` | 1 (línea 320) | sí | 121 |

Todos deben pasar por el accesor de la sección 3.

### `crud.py` — `RESOURCES`

- Los `defaults` con ceros físicos (`tcv`, `tcp`, `isc`, `y`) deben retirarse:
  el defecto correcto es NULL.
- Las listas `required` deben contener **solo** lo que la BD exige como NOT NULL,
  no lo que sería deseable. Revisar: `inverters.required` incluye hoy
  `I_max_input` e `I_max_output`, que son **nullable en el modelo** — se está
  exigiendo al usuario un dato que el esquema no requiere y que falta en 121 de
  207 inversores del catálogo.

### `memoria_service.py`

El filtro `v()` de la plantilla ya absorbe nulos, así que el documento no
revienta; el riesgo aquí es **prometer un apartado que sale vacío**. Cada
apartado debe declarar su nivel y omitirse o marcarse cuando no se alcanza.

### `installation_service.py`, `finance_service.py`

Pendientes de auditar con el mismo criterio.

---

## 6. Plan de implementación

1. **Accesor y `CapabilityResult`** en `app/services/capability.py`: primitiva
   compartida, sin dependencia de Flask.
2. **Sanear los `defaults` de `crud.py`** y alinear las listas `required` con los
   NOT NULL reales del esquema.
3. **Blindar `analysis_service`**: sustituir los 20 accesos de la tabla anterior
   y devolver nivel y `missing`.
4. **Componente `<DegradationCard>`** en `shared/ui` consumiendo `missing`.
5. **Propagación al documento**: nota de alcance en el apartado afectado.
6. **Auditar el resto de servicios** con el mismo contrato.

### Verificación prevista

- Recorrer **los 3.674 paneles y los 207 inversores** del catálogo real por el
  paso de análisis y comprobar que **ninguna combinación lanza excepción**. Es la
  prueba que hoy falla en 152 casos y la que garantiza el principio rector.
- Comprobar que ningún cálculo de seguridad (tensión máxima, corrientes) devuelve
  un número cuando falta el dato que lo condiciona: debe devolver ausencia
  declarada, no un valor optimista.

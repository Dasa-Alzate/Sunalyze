# Investigación: módulo financiero (Fase 1 — motor de cálculo)

Documento de dominio para el motor financiero de proyectos fotovoltaicos en España.
Recoge fórmulas, método numérico de la TIR y los *defaults* españoles con su fuente y
su límite honesto. El motor es puro (sin Flask) y queda **enchufable** para subvenciones
(Fase 2, reducen el CAPEX neto) y para fuentes de datos externas (curva horaria
Datadis/ESIOS) que mejorarían la precisión del autoconsumo.

## 1. Fórmulas

### Ahorro anual (año 1)
El ahorro económico anual de una instalación de autoconsumo tiene dos componentes:

```
ahorro_autoconsumo = energia_autoconsumida_kWh * tarifa_eur_kWh
ahorro_excedentes  = min(energia_excedente_kWh * precio_excedente_eur_kWh,
                         tope_RD_244_2019)
ahorro_anual       = ahorro_autoconsumo + ahorro_excedentes
```

donde:

```
energia_autoconsumida_kWh = produccion_kWh_year * self_consumption_ratio
energia_excedente_kWh     = produccion_kWh_year * (1 - self_consumption_ratio)
```

El `self_consumption_ratio` (fracción de la producción que se consume in situ) puede
venir dado o derivarse del análisis de dimensionamiento + el uplift de batería
(`analysis_service` expone `battery.estimated_self_consumption_pct`).

### Tope de compensación de excedentes (RD 244/2019)
El **valor económico de la energía horaria excedentaria no puede superar, en el periodo
de facturación, el valor económico de la energía horaria consumida de la red**
(compensación simplificada, instalaciones ≤ 100 kW). En el modelo anual lo aproximamos
como:

```
tope = energia_consumida_de_red_kWh * tarifa_eur_kWh
     = (consumo_anual_kWh - energia_autoconsumida_kWh) * tarifa_eur_kWh
```

La compensación de excedentes nunca puede dejar la factura de energía por debajo de 0 €
(no se "paga" al consumidor, solo se descuenta el término de energía).
Fuente: BOE-A-2019-5089, RD 244/2019 art. 14; resúmenes técnicos (UNEF, MITECO FAQ).

### Cashflow año a año (lifetime, default 25 años)
Para cada año `t` (1..N):

```
produccion_t      = produccion_kWh_year * (1 - degradacion)^(t-1)
tarifa_t          = tarifa_eur_kWh * (1 + escalada_tarifa)^(t-1)
precio_exc_t      = precio_excedente_eur_kWh * (1 + escalada_tarifa)^(t-1)
ahorro_t          = autoconsumo_t * tarifa_t + min(excedente_t * precio_exc_t, tope_t)
om_t              = om_cost_eur_year * (1 + escalada_tarifa)^(t-1)
cuota_prestamo_t  = cuota anual del préstamo si hay financiación y t <= plazo, si no 0
cashflow_t        = ahorro_t - om_t - cuota_prestamo_t
```

El O&M y los precios se escalan con el mismo IPC por simplicidad (parametrizable).

CAPEX neto (año 0):

```
capex_bruto   = capex_equipo + capex_mano_obra + capex_legalizacion  (o capex_total)
capex_con_iva = capex_bruto * (1 + iva_pct)
capex_neto    = capex_con_iva - sum(incentivos que reducen CAPEX)      # Fase 2
inversion_inicial_propia = capex_neto - importe_financiado
```

`incentivos` (lista, opcional) reduce el CAPEX neto o aporta cashflow en un año dado.
En Fase 1 la lista llega vacía; Fase 2 la rellenará (subvenciones IDAE/CCAA, deducción
IRPF, bonificación IBI/ICIO).

### Payback simple
Primer año en que el ahorro acumulado (sin descontar) cubre la inversión inicial propia.
Se interpola dentro del año para dar un valor fraccionario:

```
payback_simple = t-1 + (inversion_pendiente_al_inicio_de_t / cashflow_t)
```

Si nunca se recupera dentro del *lifetime* → `None` (se reporta "no se recupera").

### Payback descontado
Igual pero acumulando cashflow **descontado** a la tasa de descuento `r`:

```
cashflow_descontado_t = cashflow_t / (1 + r)^t
```

### VAN / NPV
```
NPV = -inversion_inicial_propia + Σ_{t=1..N} cashflow_t / (1 + r)^t
```
Signo positivo ⇒ proyecto rentable a la tasa `r`.

### TIR / IRR
Tasa `i` que anula el VAN del flujo completo `[CF_0, CF_1, ..., CF_N]` con
`CF_0 = -inversion_inicial_propia`:

```
0 = Σ_{t=0..N} CF_t / (1 + i)^t
```

**Método numérico (stdlib pura, sin numpy-financial):**
1. **Bisección** sobre un rango `[-0.9999, 10.0]` (−99,99 % a +1000 %). Se evalúa el NPV en
   los extremos; si tienen el mismo signo, **no hay raíz detectable** → se devuelve `None`
   con gracia (no peta). Esto cubre flujos sin cambio de signo (p. ej. todo negativo).
2. Si hay cambio de signo, se itera bisección hasta tolerancia `1e-7` o 200 iteraciones,
   y se **refina con Newton-Raphson** (derivada analítica del NPV) cuando converge dentro
   del rango; si Newton diverge, se conserva el valor de bisección.

La bisección es robusta y no requiere derivada; Newton solo afina. Se valida en tests
contra un caso resoluble a mano (ver más abajo).

**Caso de validación manual de la TIR:** flujo `[-1000, 600, 600]`.
```
0 = -1000 + 600/(1+i) + 600/(1+i)^2
```
Sustituyendo `x = 1/(1+i)`: `600 x^2 + 600 x - 1000 = 0` → `x = 0.93431...`
→ `1+i = 1.07030...` → **i ≈ 0.13066 (13,066 %)**. El test comprueba ±1e-4.

### ROI (retorno total sobre la inversión, sin descontar)
```
ROI = (Σ cashflow_t - inversion_inicial_propia) / inversion_inicial_propia
```

### LCOE (coste nivelado de la energía)
Coste por kWh producido a lo largo de la vida, descontando costes y energía:

```
LCOE = (inversion_inicial_propia + Σ_{t=1..N} costes_t/(1+r)^t)
       / Σ_{t=1..N} produccion_t/(1+r)^t
```
donde `costes_t = om_t + cuota_prestamo_t` (los excedentes/ahorros NO entran en el LCOE;
es coste de generar, no de ahorrar). Unidad: €/kWh.

### CO₂ evitado
```
co2_evitado_anual_kg   = produccion_kWh_year * factor_emision_kg_kWh
co2_evitado_lifetime_kg = Σ_{t} produccion_t * factor_emision_kg_kWh
```
Se usa la producción autoconsumida + vertida (toda la producción desplaza red).

## 2. Defaults españoles (con fuente y límite honesto)

| Parámetro | Default | Fuente | Límite honesto |
|---|---|---|---|
| `tariff_eur_kwh` | 0,15 €/kWh | Orden de magnitud PVPC medio doméstico 2024-2025 | El PVPC es **horario**; un único valor medio ignora la discriminación horaria. La precisión fina exige curva horaria (ESIOS). |
| `surplus_price_eur_kwh` | 0,06 €/kWh | Precio típico de compensación de excedentes de comercializadoras (mercado libre/PVPC excedentes) | Varía por comercializadora y hora; sujeto al tope RD 244/2019. |
| `tariff_escalation_pct` (IPC) | 0,025 (2,5 %/año) | Objetivo de inflación BCE ~2 % + histórico energético | La energía ha sido más volátil que el IPC general; es un supuesto, no una predicción. |
| `panel_degradation_pct` | 0,005 (0,5 %/año) | Garantías de fabricantes Tier-1 (degradación lineal típica) | Primer año suele ser mayor (~2 %); modelamos lineal por simplicidad. |
| `discount_rate` | 0,04 (4 %) | Coste de oportunidad doméstico/PYME conservador | Subjetivo; afecta mucho a VAN/payback descontado. |
| `factor_emision_kg_kWh` | 0,25 kg CO₂/kWh | Mix eléctrico nacional ES ~0,25-0,28 kgCO₂e/kWh (MITECO/OECC 2024-2025) | El factor baja cada año con más renovables; es un valor medio anual, no marginal horario. |
| `iva_pct` | 0,21 (21 %) | IVA general España | Algunas CCAA/casos tienen IVA reducido o bonificaciones; configurable. |
| `lifetime_years` | 25 | Vida útil estándar garantizada de módulos FV | El inversor suele requerir reemplazo (~12-15 años); se puede modelar vía O&M. |
| `om_cost_eur_year` | 0,0 (o ~1 % CAPEX) | Mantenimiento residencial bajo | Para plantas mayores el O&M es significativo. |

**Nota honesta sobre el autoconsumo:** el reparto autoconsumo/excedente real depende de la
**coincidencia horaria** entre la curva de generación FV y la curva de consumo del cliente.
Un `self_consumption_ratio` único (medio anual) es una aproximación. La cifra precisa
requiere datos horarios reales de consumo (Datadis) y de generación (PVGIS horario / ESIOS).
El motor recibe `production_kwh_year` + `self_consumption_ratio` como **puntos de enchufe**:
una fuente horaria futura solo tiene que calcular mejor ese ratio y/o sustituir el bloque de
ahorro anual por una integral horaria, sin tocar las métricas financieras.

## 3. Fuentes
- BOE-A-2019-5089, Real Decreto 244/2019 (autoconsumo, compensación simplificada de excedentes y su tope): https://www.boe.es/buscar/doc.php?id=BOE-A-2019-5089
- UNEF, resumen RD 244/2019: https://autoconsumo.unef.es/real-decreto-244-2019/
- MITECO, FAQ autoconsumo: https://www.miteco.gob.es/en/energia/energia-electrica/electricidad/autoconsumo-electrico/preguntas-frecuentes-autoconsumo.html
- MITECO / OECC, factores de emisión del mix eléctrico 2024 (~0,283 kgCO₂e/kWh) y 2025 (~0,258): https://www.miteco.gob.es/content/dam/miteco/es/cambio-climatico/temas/mitigacion-politicas-y-medidas/factoresemision_tcm30-542746.xlsx
- IDAE, factores de conversión y emisiones de CO₂: https://sede.idae.gob.es/sites/default/files/2024-02/Factores_de_conversion_ahorros_y_emisiones_de_CO2.pdf

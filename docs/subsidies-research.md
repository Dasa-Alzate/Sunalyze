# Investigación: subvenciones e incentivos al autoconsumo FV en España (Fase 2)

Documento de dominio para el catálogo de incentivos que alimenta el CAPEX neto del motor
financiero (Fase 1). Recoge cada incentivo con su porcentaje/importe/tope típico, su fuente
normativa y su variabilidad territorial. El motor consume `Incentive`
(`kind=capex_reduction|cashflow`, `amount`, `year`): un incentivo que abarata la instalación
se modela como `capex_reduction` (resta del CAPEX neto) o como `cashflow` de un año fiscal
concreto; un incentivo plurianual (bonificación de un tributo durante N años) se reparte como
varios `cashflow`.

Regla transversal: los incentivos en España **no son acumulables sin límite**. La deducción
IRPF y las ayudas Next Generation se solapan parcialmente y la base de la deducción debe
minorarse en la subvención recibida. Aquí se modelan como capas aditivas con defaults
prudentes; el ajuste fino de incompatibilidades queda como límite honesto (ver §6).

## 1. Deducción en el IRPF (estatal)

**Fuente:** Real Decreto-ley 19/2021, de 5 de octubre, de medidas urgentes para impulsar la
actividad de rehabilitación edificatoria (introduce las disposiciones adicionales quincuagésima
de la Ley 35/2006 del IRPF). Prorrogada sucesivamente; vigente para obras hasta 31/12/2025
(prórroga por RD-ley posterior; comprobar fecha de devengo al aplicar).

Tres tramos según la mejora de eficiencia energética acreditada por certificado:

| Tramo | Requisito (certificado energético) | % deducción | Base máxima anual |
|-------|------------------------------------|-------------|-------------------|
| 20%   | Reducción ≥ 7% demanda calefacción/refrigeración | 20% | 5.000 € |
| 40%   | Reducción ≥ 30% consumo energía primaria no renovable | 40% | 7.500 € |
| 60%   | Vivienda en edificio de uso residencial; mejora del edificio | 60% | 5.000 €/año, hasta 15.000 € en 4 años |

- La base de la deducción son las cantidades satisfechas por las obras, **minoradas en el
  importe de subvenciones públicas recibidas** para las mismas obras.
- El autoconsumo FV encaja típicamente en el tramo del **40%** (reduce consumo de energía
  primaria no renovable) cuando se acredita por certificado antes/después; sin certificado no
  hay derecho a deducción.
- Se aplica en la declaración de la renta del ejercicio del pago → en el motor es naturalmente
  un `cashflow` del **año fiscal** (año 1 o 2), aunque modelarlo como `capex_reduction`
  (abarata la inversión efectiva) es una simplificación aceptable para payback/TIR.

**Default modelado:** tramo 40%, base máxima 7.500 € → deducción máx. 3.000 €, tope sobre el
CAPEX con IVA. Conservador y nacional (aplica en todo el territorio común; País Vasco y Navarra
tienen IRPF foral con deducciones propias distintas → no se modelan).

## 2. IVA reducido

**Fuente:** Ley 37/1992 del IVA, tipos reducidos para obras en vivienda. El autoconsumo
doméstico tributa normalmente al tipo general (21%) salvo encaje en obras de
renovación/rehabilitación con materiales limitados.

**No se modela como incentivo aparte:** el IVA ya entra en el CAPEX del motor
(`capex_with_vat = gross_capex * (1 + iva_pct)`), con default 21%. Reducirlo se hace bajando
`iva_pct` en los supuestos, no añadiendo un `Incentive`.

## 3. Bonificación del IBI (municipal)

**Fuente:** Real Decreto Legislativo 2/2004, Texto Refundido de la Ley Reguladora de las
Haciendas Locales (TRLRHL), art. 74.5 — faculta (no obliga) a los ayuntamientos a bonificar
**hasta el 50%** de la cuota del IBI a inmuebles con sistemas de aprovechamiento de energía
solar, durante el número de años que fije la ordenanza fiscal municipal.

- Es **potestativo y muy variable por municipio**: el % (típico 25–50%) y la duración
  (típico 3–5 años, a veces hasta 10 o 30) se fijan en la ordenanza fiscal local.
- Depende de la cuota del IBI del inmueble (que depende del valor catastral) → en el motor se
  modela como `cashflow` anual = `cuota_IBI * pct_bonif`, **repartido en N años** (un
  `Incentive` cashflow por cada año bonificado).
- Sin conocer el municipio no hay bonificación por defecto (capa MUNICIPIO opcional).

**Defaults de ejemplo modelados (capa MUNICIPIO, editables):**
- Madrid: 25% durante 3 años.
- Barcelona: 50% durante 3 años.
- Valencia: 50% durante 5 años.
Importes ilustrativos sobre una cuota IBI estimada; la cuota real la aportaría el usuario.

## 4. Bonificación del ICIO (municipal)

**Fuente:** TRLRHL art. 103.2.b — faculta a los ayuntamientos a bonificar **hasta el 95%** de
la cuota del Impuesto sobre Construcciones, Instalaciones y Obras para instalaciones de
aprovechamiento de energía solar, en las condiciones de la ordenanza.

- El ICIO es un tributo **único** ligado a la licencia/declaración de obra (no plurianual) →
  `cashflow` del año 1 (o `capex_reduction`).
- Base = coste de ejecución material de la obra; bonificación típica 50–95%.
- Igualmente potestativo y variable por municipio.

**Defaults de ejemplo modelados (capa MUNICIPIO):** Madrid 95%, Barcelona 50%, Valencia 50%
sobre un ICIO estimado proporcional al CAPEX. Ilustrativo.

## 5. Fondos Next Generation EU — autoconsumo

**Fuente:** Real Decreto 477/2021, de 29 de junio, por el que se aprueba la concesión directa
de ayudas a CCAA para programas de incentivos al autoconsumo, almacenamiento y climatización
con renovables (fondos del PRTR / Next Generation EU). Gestionados y convocados por cada
**Comunidad Autónoma** (IDAE coordina).

- Programa 1–2 (autoconsumo sector servicios) y 4–5 (autoconsumo/almacenamiento sector
  residencial, AAPP y tercer sector).
- Modalidad **€/kWp** o **% del coste subvencionable**, con módulos de referencia:
  - FV sin almacenamiento, residencial (Programa 4): ~**600 €/kWp** (tramos por potencia,
    decreciente a mayor potencia).
  - Plus por almacenamiento: ~**490 €/kWh** instalado.
  - Sector servicios: ~15–45% del coste según tamaño.
- Se concede como subvención directa al beneficiario → en el motor `capex_reduction`.
- **Variabilidad alta:** depende de la CCAA, de la convocatoria abierta y del agotamiento del
  presupuesto. Muchos programas cerraron al agotarse fondos en 2024.

**Defaults modelados:**
- Capa NACIONAL: módulo base RD 477/2021 residencial, ~600 €/kWp con tope (p. ej. 3.000 € o
  un % del CAPEX), como suelo común.
- Capa CCAA: posibilidad de ajustar el €/kWp o el tope por comunidad (ejemplos en el catálogo).

## 6. Variabilidad territorial y límite honesto

- **IRPF:** estatal y homogéneo en territorio común, pero requiere certificado energético y
  minoración de base por otras subvenciones. País Vasco/Navarra tienen IRPF foral propio (no
  modelado).
- **IBI/ICIO:** 100% dependientes de la ordenanza fiscal de cada uno de los >8.000 municipios.
  Los defaults de Madrid/Barcelona/Valencia son ilustrativos y deben confirmarse con la
  ordenanza vigente; la cuota concreta depende del valor catastral del inmueble.
- **Next Generation:** depende de convocatoria abierta por CCAA y de presupuesto disponible;
  los módulos €/kWp son de referencia del RD 477/2021 y no garantizan concesión.
- **Acumulación:** las incompatibilidades reales (minorar base IRPF por la subvención NextGen,
  topes de intensidad de ayuda de la UE) **no se modelan**; el catálogo suma capas. El
  resultado debe leerse como "mejor caso indicativo", no como liquidación fiscal.

## 7. Estructura de capas (resumen para implementación)

Mismo patrón que `app/scrapers/acceptance.py`: resolución por especificidad creciente.

```
NACIONAL                → IRPF (capex_reduction, con tope) + Next Gen base (€/kWp, con tope)
CCAA[<ccaa>]            → ajuste del €/kWp Next Gen / topes por comunidad
MUNICIPIO[<municipio>]  → IBI (cashflow repartido N años) + ICIO (cashflow año 1)
```

`SubsidyService.applicable(project, capex, system_kwp, ccaa=None, municipio=None)` devuelve la
lista de `Incentive` que el motor ya consume. Sin territorio conocido, solo aplican los
incentivos nacionales.

# Perfil de consumo — investigación (CDM)

Complemento factual de `docs/perfil-consumo-cdm-sintesis.md` (las decisiones viven allí).

## Formatos de archivo del mercado español

**Datadis / e-distribución (curva horaria).** CSV con separador `;`, decimal con coma.
Columnas típicas: `CUPS;Fecha;Hora;Consumo_kWh;Metodo_obtencion` (Datadis usa `consumptionKWh`
y fechas `YYYY/MM/DD`; e-distribución `DD/MM/YYYY`). La hora es **hour-ending 1..24**
(la fila "1" es el consumo de 00:00–01:00). `Metodo_obtencion` = R (real) / E (estimada) — se ignora.

**Curva cuartohoraria.** Mismo esquema con 96 filas/día (`Hora` 1..96 o `HH:MM`); se agrega a
horaria por suma de los 4 cuartos (los valores cuartohorarios son kWh del cuarto, no potencia media).

**Cambio de hora (DST).** El día de marzo tiene 23 horas y el de octubre 25 (Datadis numera hasta 25).
Normalización: marzo → la hora ausente se interpola como media de las adyacentes; octubre → las dos
horas repetidas se promedian. El error introducido es de 1-2 h sobre 8.760: despreciable.

**Año bisiesto en origen:** descartar 29-feb.

**Adapter tolerante:** sniff de separador (`;` o `,`), decimal coma→punto, detección de columnas por
cabecera (patrones `fecha|date`, `hora|period|time`, `consumo|consumption|kwh|valor`), filas de
cabecera/vacías ignoradas. No atarse a un vendor exacto.

**JSON del cuaderno del asesor:** lista de registros `{mes, dia, hora, consumo_kwh, ...}` con
hora 0..23 (hour-beginning, a diferencia de los CSV). 8.760 registros.

## Calendario canónico

Año 2018: no bisiesto y el 1 de enero fue lunes (verificado). Día-del-año `d` (1..365);
tipo de día por `(d-1) % 7`: 0..4 laborable, 5 sábado, 6 domingo — correcto SOLO bajo esta convención.
Anclas estacionales: invierno `d=15` (15-ene), verano `d=196` (15-jul).

## Matriz intermedia: la celda lleva forma Y peso

Hallazgo del análisis: la forma de 24h no basta cuando la muestra es medida — un día de invierno
consume más kWh totales que uno de verano, y un sábado distinto que un laborable. La celda es:

```
celda = { forma: [24 fracciones, suman 1], peso: total_diario_relativo }
```

Con muestras medidas, `peso` = kWh totales del día muestreado (relativo entre celdas).
Con formas dibujadas en UI, `peso = 1` para todas (solo forma). Así una semana medida de
invierno + una de verano preservan tanto la forma intradía como el nivel estacional.

## Interpolación estacional

Peso de verano en el día `d`: `w(d) = 0.5 · (1 − cos(2π · (d − 15) / 365))` — vale 0 en el
ancla de invierno (d=15) y ~1 en verano (d≈197). Para cada día:

```
forma_d  = (1−w)·forma_inv + w·forma_ver      (por tipo de día del calendario canónico)
peso_d   = (1−w)·peso_inv  + w·peso_ver
serie[h] = peso_d · forma_d[h]
```

Con una sola ancla, `w=0` siempre (forma plana todo el año). Al final:
`fracciones = serie / sum(serie)` → invariante `sum(8760) == 1.0`.

## Formas curadas de semilla (dominio, valores aproximados de literatura REE/IDAE)

- **Residencial tarde-noche**: valle nocturno, pico 20-22h, hombro mediodía; invierno más
  cargado (calefacción) → peso_inv > peso_ver.
- **Residencial teletrabajo**: meseta 9-18h + pico cena.
- **PYME oficina L-V**: campana 8-18h, finde plano casi nulo, estacionalidad leve (AC verano).
- **Comercio con fin de semana**: campana 10-21h los 7 días, sábado el más alto.
- **Industrial 2 turnos**: meseta 6-22h laborables, finde reducido.
- **Bombeo/riego diurno**: campana solar (10-18h), verano ≫ invierno (peso_ver alto) —
  el caso donde FV rinde máximo sin batería.

Los valores exactos se declaran en un JSON de semilla; son estimaciones editables, no medidas.

# CDM de perfiles de consumo — síntesis de conclusiones

Documento de trabajo para Claude. No es spec: son las decisiones ya tomadas en el brainstorm
del 2026-09-26 con David, para retomarlas en la implementación sin re-deliberar.
Origen: cuaderno del asesor (`Funciones_Bateria.ipynb`) + arreglos acordados.

## La decisión central: dos capas, no una

**Capa 1 — `ProfileSource` (lo que el usuario entregó, intacto):** kind + payload JSON + metadata
de procedencia. Nunca se pierde: permite re-materializar cuando mejoren las reglas de expansión
y editar desde la UI lo mismo que se importó.

**Capa 2 — canónico materializado: 8.760 FRACCIONES horarias (suman 1.0) + `annual_kwh` aparte.**
El motor consume siempre esto y solo esto. Fracciones y no kWh porque separa FORMA de ESCALA:
el mismo perfil (forma) sirve a proyectos con consumos anuales distintos, la librería curada
son formas puras, y cambiar el kWh anual del proyecto no obliga a re-importar nada.
`kwh[h] = fraccion[h] × annual_kwh` — el annual_kwh vive en el PROYECTO (el perfil solo
lleva un `annual_kwh_hint` si el origen era medido).

## Análisis de dimensionalidad → qué es dimensión real y qué no

| Eje | Conclusión |
|---|---|
| Origen (UI / archivo) | NO es dimensión del modelo — es el adapter de entrada. Ambos producen el mismo `ProfileSource`. |
| Tamaño de muestra (día/semana/mes/año) | SÍ — determina qué celdas de la matriz intermedia se rellenan. |
| Estacionalidad (1 temporada / verano+invierno) | SÍ — determina cuántas anclas estacionales hay. |
| Tipo de día (laborable/sábado/domingo) | SÍ, pero DERIVADA del tamaño: un día no la trae, una semana o mes sí. |
| Resolución (horaria / cuartohoraria) | NO es dimensión — se agrega a horaria en el import (media de los 4 cuartos). |
| Absoluto (kWh medidos) vs patrón (forma) | NO es dimensión — un absoluto es una forma + un hint de escala. |

## La representación intermedia que colapsa todos los casos

Todo import se reduce a rellenar celdas de una **matriz día-tipo × temporada de formas de 24h**:

```
day_types:  laborable | sabado | domingo
seasons:    anclas en día-del-año (p. ej. invierno=15-ene, verano=15-jul)
celda:      24 fracciones (suman 1.0)
```

Reglas de reducción por kind:
- `annual_8760` → BYPASS de la matriz: fracciones directas (valores/suma). El caso rico no se degrada.
- `week` (7 días) → promedia lun-vie → laborable; sab; dom. 1 ancla estacional (fecha de la muestra o "sin fecha").
- `month` → igual que week (agrupa por día de semana real del mes), 1 ancla.
- `day` → la misma forma para los 3 day_types, 1 ancla.
- `seasonal` (día o semana de verano + de invierno) → 2 anclas.
- `curated_ref` → apunta a un perfil global ya materializado.

Celdas ausentes: copia de la celda más cercana provista (día→los 3 tipos; sin regla de atenuación
de finde inventada — YAGNI, el usuario que quiera finde distinto entrega una semana).

## Expansión matriz → 8.760

- **Calendario canónico fijo: año no bisiesto que empieza en LUNES** (usar el calendario de 2018).
  Esto mata por convención el bug del cuaderno (`(dia_ano-1) % 7` asumía eso sin decirlo).
  Festivos: fuera de v1 (anotado como mejora; en 2.0TD los festivos nacionales son valle).
- Con 1 ancla estacional: forma plana todo el año.
- Con 2 anclas: **interpolación sinusoidal diaria** entre la forma de invierno y la de verano
  (peso = coseno sobre día-del-año centrado en las anclas). Suave, barato, sin escalones en los
  cambios de temporada. Con 12 anclas mensuales (futuro) la misma interpolación generaliza.
- Renormalizar al final: sum(8760) = 1.0 exacto.
- **Determinismo absoluto: CERO ruido aleatorio** (el ±5% del cuaderno hace irreproducibles
  presupuestos y tests). La variación real ya viene en los datos medidos.
- Guardar `cdm_version` en el materializado; si cambia la lógica de expansión, re-materializar
  desde el source en el siguiente uso.

## Imports (adapters, todos → ProfileSource)

- **UI**: editor de forma de 24h (sliders/tabla) por day_type y temporada — produce `day`/`seasonal`.
- **Archivo CSV del distribuidor** (Datadis / e-distribución, cuartohorario): parsear, agregar a
  horario, **descartar 29-feb**, normalizar los días de 23/25h del cambio DST a 24h (repartir/promediar),
  mapear al calendario canónico por día de semana real → produce `annual_8760` o `month`.
- **JSON del cuaderno** (formato del asesor, lista de registros con `consumo_kwh`): soportarlo como
  cortesía de import, mismo destino.

## Perfiles curados

Mismo modelo, `org_id = NULL` = global (mismo patrón que los catálogos oficiales de equipos).
Semilla inicial (formas, sin escala): residencial tarde-noche, residencial teletrabajo,
PYME oficina L-V, comercio con fin de semana, industrial 2-3 turnos, bombeo/riego diurno.
Se entregan como `seasonal` (verano+invierno) para que la interpolación luzca.

## Encaje en Sunalyze

- Modelo: `app/models/consumption_profile.py` — org-scoped + globales, soft-delete como el resto.
- Servicio: `app/services/consumption/` — `expanders.py` (reducción por kind + expansión a 8760),
  `imports.py` (adapters CSV/JSON). El parseo NO vive en el modelo.
- Proyecto: FK `consumption_profile_id` (nullable — sin perfil, el análisis sigue como hoy)
  + el `necesidad` (kWh anual) existente del proyecto ES la escala. No duplicar.
- El motor horario (balance batería + económico) consume `(fracciones_8760 × necesidad, pvgis_horario)`.

## Encaje UX (decidido con David, 2026-09-26)

- **Sin paso nuevo en el wizard.** Sección «Perfil de consumo» DENTRO del paso 1 «Lugar»,
  pegada al campo `necesidad`, con las tres vías in situ: elegir (curados + de la org),
  subir CSV, o dibujar la forma 24h. El caso dominante es un perfil único por proyecto:
  el instalador no sale del wizard para crearlo.
- Lo creado in situ se persiste como perfil de la organización (nombre por defecto derivado
  del cliente del proyecto) → el reuso sale gratis.
- La **biblioteca** (pestaña en Equipos o sección propia) es solo la vista de GESTIÓN
  (renombrar, clonar, borrar, ver uso) — no un segundo flujo de creación. Un solo camino
  de escritura, dos puntos de acceso.
- El fruto se muestra en el paso «Análisis» (bloque económico horario si hay perfil) y a
  futuro el barrido de escenarios en Finanzas.

## Impacto y visión recomendador (David, 2026-09-26)

- La meta del sistema es RECOMENDAR equipos (del catálogo disponible), compararlos entre sí
  y estimar ahorro contra la factura del cliente. El barrido de escenarios del cuaderno es
  el embrión de ese recomendador (potencia × batería × inversor → ahorro anual y payback
  con los precios tarifa del catálogo).
- Con perfil, el `autoconsumo` deja de ser input declarado en el paso 1 y pasa a ser
  RESULTADO del cruce horario. Migración de UX a diseñar cuando llegue el motor.
- La batería solo es dimensionable/justificable con perfil — su valor es la dimensión temporal.
- **Nunca hay estado "sin perfil" para el recomendador**: sin perfil propio se usa un curado
  por defecto según tipo de cliente, etiquetado «estimación con perfil genérico». La ausencia
  de perfil degrada precisión, no funcionalidad. El CSV real es el upgrade natural del flujo
  de venta (visita 1: curado; cierre: Datadis del cliente).

## FUERA del CDM (fronteras explícitas, van en el motor económico)

1. Tarifas y periodos (2.0TD/3.0TD, festivos, precios) — modelo aparte; el CDM no sabe de precios.
2. Batería: límite de potencia C-rate/inversor — arreglo pendiente al simulador del cuaderno.
3. Contrafactual del ahorro de batería (precio_excedente como coste de oportunidad, y 0 cuando
   la hucha satura) y NO tratar el saldo de hucha como dinero cobrable.
4. Producción FV sintética del cuaderno: NO se porta — se usa la serie horaria real de PVGIS
   (con horizonte y zonas de REONIC).

## Errores del cuaderno que este diseño neutraliza (para contárselo al asesor)

- Finde por `% 7` sin anclar el calendario → calendario canónico lunes-primero.
- Ruido aleatorio → determinismo.
- 2.0TD con 17 kW contratados (imposible, tope 15 kW) → la tarifa es del motor económico, parametrizada.
- Producción FV sintética → PVGIS real.

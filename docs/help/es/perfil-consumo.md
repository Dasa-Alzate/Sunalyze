---
title: Perfil de consumo del cliente
routes:
  - equipos/perfiles
order: 33
keywords: [perfil, consumo, curva, horaria, datadis, csv, bateria, autoconsumo, factura, valle, punta]
---

# Concepto

El perfil de consumo describe **cómo se reparte el consumo eléctrico del cliente a lo largo del año**, hora a hora. No es cuánto consume (eso lo dice el consumo anual del proyecto), sino *cuándo*: si la casa gasta por la noche, si la oficina solo vive de lunes a viernes, si el riego dispara en verano.

Esa dimensión temporal es la que permite calcular el ahorro real: la producción solar de mediodía solo vale lo que el cliente consume (o almacena) en ese momento.

:::cards
- **Forma** — el reparto horario del consumo, normalizado. Es lo que guarda el perfil.
- **Escala** — los kWh anuales del proyecto. Se define en el proyecto, no en el perfil.
- **Perfil curado** — forma típica lista para usar (residencial, oficina, comercio, industrial…).
:::

:::tip{tone=info title="El aporte de la batería depende del perfil"}
Sin perfil, una batería no tiene valor calculable: su beneficio es exactamente el desfase entre cuándo produce el sol y cuándo consume el cliente. Con perfil, el sistema puede cuantificar cada kWh desplazado de las horas valle de producción a las horas punta de consumo.
:::

# Criterio

## Qué muestra entregar

Cuanto más real sea la muestra, más finos los números:

:::cards
- **Curva anual del contador** — la mejor: el CSV de Datadis o de la distribuidora (8.760 horas medidas).
- **Verano + invierno** — dos muestras (día o semana) capturan la estacionalidad; el sistema interpola el resto del año.
- **Una semana** — distingue laborables de fin de semana.
- **Un día** — el mínimo: la misma forma todos los días.
- **Perfil curado** — sin datos del cliente, elige la forma típica más parecida y refina después.
:::

## Convenciones del cálculo

:::callout{tone=info}
El perfil se normaliza a un año canónico de 365 días que empieza en lunes, sin festivos. El 29 de febrero y los cambios de hora del CSV se corrigen automáticamente. El resultado es determinista: la misma muestra produce siempre el mismo perfil.
:::

# Flujo

:::flow
- **Obtener la muestra** — CSV del contador (Datadis) o conocimiento del uso del cliente.
- **Crear el perfil** — subir el archivo o dibujar la forma; queda guardado en la organización.
- **Asociarlo al proyecto** — junto al consumo anual del cliente.
- **Cosechar** — el análisis cruza producción y consumo hora a hora: autoconsumo real, aporte de la batería y ahorro en factura.
:::

# Tutorial

## Importar la curva del contador

:::steps
1. Pide al cliente su curva horaria en **Datadis** (datadis.es, con su DNI y CUPS) o en el área privada de su distribuidora, y descarga el CSV.
2. Sube el archivo en la sección **Perfil de consumo**: se admite CSV horario o cuartohorario, de un año completo o de un mes natural.
3. Revisa el nombre del perfil (por defecto toma el del archivo) y guárdalo: queda disponible para este y futuros proyectos. Los perfiles se gestionan en la pestaña **Perfiles** de la biblioteca de **Equipos**.
:::

:::callout{tone=warning}
Si el CSV está incompleto (faltan días del mes), el sistema lo rechaza indicando qué días faltan. Descarga de nuevo el rango completo.
:::

## Sin datos del cliente

:::steps
1. Elige un **perfil curado** que se parezca al uso real: residencial tarde-noche, teletrabajo, oficina, comercio, industrial o riego.
2. O dibuja la forma a mano: consumo relativo por hora, con variantes para sábado, domingo y por temporada.
3. Cuando el cliente comparta su CSV real, crea el perfil medido y sustitúyelo en el proyecto: los cálculos se refinan sin tocar nada más.
:::

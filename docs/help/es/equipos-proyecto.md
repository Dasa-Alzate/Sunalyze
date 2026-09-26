---
title: Equipos del proyecto
routes:
  - diseno/equipos
order: 31
keywords: [equipos, panel, inversor, bateria, cable, cableado, catalogo, seleccion]
---

# Concepto

El paso **Equipos** vincula los equipos del catálogo al proyecto concreto. Lo que elijas aquí determina qué dimensionamiento calcula el análisis, qué esquema genera el diagrama unifilar y qué fichas técnicas aparecen en la memoria.

:::cards
- **Panel solar** — obligatorio. Define la potencia, tensiones y dimensiones de cada módulo.
- **Inversor** — opcional en este paso; puedes dejarlo vacío y el análisis te ofrecerá una lista de compatibles.
- **Batería** — opcional. Si la incluyes, el análisis calcula banco, autonomía y aporte anual.
- **Cableado** — opcional. Sección y material de los cables CC, CA y de tierra; alimenta la memoria técnica.
:::

## Buscador de equipos

Cada selector es un campo de búsqueda en tiempo real: escribe parte del nombre, la potencia o cualquier dato y la lista se filtra al instante. Navega con las teclas ↑ ↓ y confirma con Intro, o haz clic en la fila.

:::tip{tone=info title="Sin inversor fijado"}
Dejar el **Inversor** en blanco es la opción recomendada si aún no lo has decidido. El análisis calcula el rango de tensiones de cadena y muestra una tabla de **Inversores compatibles** con su margen de tensión — elige directamente desde ahí.
:::

# Criterio

## Compatibilidad del inversor

El análisis comprueba la ventana MPP: la tensión de cadena en frío (Voc × N módulos × factor de temperatura) no debe superar la **V máxima** del inversor; en caliente, la tensión MPP mínima debe quedar por encima del umbral inferior.

Si fijas un inversor que no cumple, el cálculo lo indica. Puedes marcar **Mostrar todos los inversores compatibles (desactivar filtro por potencia)** para ver toda la biblioteca sin filtrar por potencia y elegir manualmente.

## Batería y cantidad

Cuando seleccionas batería, aparece el campo **Cantidad de baterías**. El análisis multiplica la capacidad nominal por esa cantidad para calcular el banco total y la energía útil.

# Tutorial

## Seleccionar los equipos

:::steps
1. Haz clic en el buscador **Panel solar** y escribe el modelo o la potencia; selecciona el módulo de la lista.
2. Si ya sabes qué inversor usas, búscalo en **Inversor**; si no, déjalo vacío.
3. Si el proyecto incluye almacenamiento, busca la batería en **Batería** y ajusta la **Cantidad de baterías**.
4. En la sección **Cableado**, selecciona la sección para **Cable CC (serie fotovoltaica)**, **Cable CA (salida del inversor)** y **Cable de tierra** si la memoria técnica los requiere.
5. Pulsa **Calcular y continuar** — el wizard lanza el dimensionamiento y avanza al paso **Análisis**.
:::

:::tip{tone=success}
Para borrar la selección de inversor, batería o cable pulsa la × que aparece a la derecha del buscador cuando hay algo elegido.
:::

:::callout{tone=info}
Si el panel no aparece en el catálogo, ve a **Equipos › Paneles** en la barra lateral para añadirlo antes de volver al diseño.
:::

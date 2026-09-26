---
title: Disposición de módulos
routes:
  - diseno/disposicion
order: 40
keywords: [disposicion, zonas, aguas, strings, sombras, heatmap, filas]
---

# Concepto

La disposición traduce el dimensionado del análisis a una colocación real sobre la cubierta: dónde cabe cada módulo, cómo se agrupan en strings y cuánta producción pierdes por sombras y orientación.

## Zonas: una por agua de cubierta

Cada zona representa un agua (faldón) con su propio plano: azimut, inclinación y si los módulos van coplanares o en estructura inclinada.

:::cards
- **Zona** — polígono de cubierta con plano propio y sus filas de módulos.
- **Exclusiones** — áreas donde no se puede montar (claraboyas, retranqueos).
- **Obstáculos** — elementos con altura que proyectan sombra (chimeneas, antenas).
:::

:::tip{tone=info title="Cubiertas a varias aguas"}
Crea una zona por agua con «Añadir zona». La producción se calcula por zona con su azimut e inclinación reales, no con un único plano medio.
:::

# Criterio

## Separación entre filas

En cubierta plana (no coplanar), la separación IDAE evita que una fila sombree a la siguiente en el mediodía de invierno.

:::norm{code="IDAE PCT-C-REV"}
La distancia mínima entre filas se calcula con **d = h / tan(61° − latitud)**, donde *h* es la altura del obstáculo (la propia fila delantera).
:::

:::callout{tone=warning}
Reducir la separación por debajo de la recomendada gana módulos pero pierde producción anual por sombreado mutuo. La pantalla de opciones cuantifica ese intercambio antes de que decidas.
:::

## Strings

Los módulos se agrupan en strings por color. Un string debe quedar dentro de la ventana MPP del inversor: la suma de tensiones de sus módulos en frío no puede superar la V máxima, ni quedar por debajo del mínimo MPP en caliente.

# Flujo

:::flow
- **Dibujar la cubierta** — traza el polígono del agua sobre el mapa.
- **Configurar el plano** — azimut, inclinación y coplanar/estructura.
- **Auto-colocar** — rellena la zona con la separación recomendada.
- **Ajustar** — celdas a mano, exclusiones y obstáculos.
- **Strings** — agrupa y comprueba contra la ventana MPP.
:::

# Tutorial

## Colocar los módulos

:::steps
1. Pulsa **Dibujar cubierta** y marca el perímetro del agua; cierra el polígono en el primer vértice.
2. Ajusta el plano de la zona: azimut (180° = sur), inclinación y coplanar si va sobre teja.
3. Pulsa **Auto-colocar**: la rejilla usa la separación IDAE en plana y 2 cm en coplanar.
4. Pinta o borra celdas sueltas con el ratón para adaptar la mancha a la realidad.
5. Añade **obstáculos** con su altura: el mapa de sombras se recalcula al momento.
:::

:::screenshot{src=diseno/disposicion.png alt="Editor de disposición con zonas y heatmap"}
Editor con dos zonas, obstáculos y el mapa anual de sombras activo.
:::

## Si no caben los módulos del análisis

:::steps
1. Cuando el área no alcanza, aparece **Ver opciones** con alternativas cuantificadas.
2. Compara: añadir otra zona, apretar filas (+módulos, −producción), girar orientación, subir potencia de módulo o aceptar menos módulos.
3. Al elegir módulo más potente vuelves a **Equipos** con el mínimo de W ya calculado.
:::

:::tip{tone=success}
La producción del análisis se realimenta con lo realmente colocado: si cambias la disposición, el paso de análisis refleja la nueva producción por zona.
:::


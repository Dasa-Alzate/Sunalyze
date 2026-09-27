---
title: Ahorro económico y gráficas de decisión
order: 34
keywords: [ahorro, factura, economia, barrido, rentabilidad, payback, inversion, bateria, tarifa, autoconsumo, graficas]
---

# Concepto

El bloque **Ahorro económico** del paso Análisis cruza el perfil de consumo del cliente con la producción solar **hora a hora durante un año completo** y traduce el resultado a euros: la factura de hoy, la factura con el sistema y lo que aporta cada equipo.

La diferencia con el dimensionado clásico está en una cifra: el **autoconsumo real**. Deja de ser el porcentaje que tú declaras en el paso 1 y pasa a ser un resultado calculado — la fracción del consumo que de verdad coincide (o se almacena) con las horas de sol de *ese* cliente.

:::cards
- **Factura sin placas** — lo que el cliente paga hoy con la tarifa de tu organización (2.0TD por defecto). Es también el techo teórico de ahorro.
- **Factura con el sistema** — misma tarifa, restando autoconsumo, batería y compensación de excedentes mes a mes.
- **Aporte de la batería** — la diferencia real de factura anual entre el sistema con y sin ella. Una sola cifra, con impuestos incluidos.
:::

:::callout{tone=info}
La compensación de excedentes respeta la regla real: descuenta como máximo hasta dejar la factura del mes en cero, y el sobrante se arrastra pero nunca se cobra. Si ves el aviso de excedentes que no llegan a descontarse, ahí hay margen para más batería o menos campo.
:::

# Criterio

Cada pestaña del bloque responde una decisión concreta. Léelas así:

## Barrido — ¿cuántos kWp?

Ahorro anual frente a potencia del campo, una curva por batería. Busca el **codo**: donde la curva se aplana, cada kWp extra aporta poco. La línea discontinua es el **ahorro máximo** (la factura actual): acercarse a ella con holgura suele significar sobredimensionado.

## Rentabilidad — ¿dónde está el punto dulce?

Ahorro anual frente a **inversión inicial estimada** (equipos del proyecto a precio de catálogo + mano de obra de tu organización). Las diagonales marcan paybacks de 3, 5 y 8 años: cuanto más arriba-izquierda quede un punto, mejor. La tabla inferior compara las baterías con el campo actual.

:::callout{tone=warning}
Las baterías sin precio unitario en el catálogo quedan fuera de esta gráfica (se listan debajo): estimar una inversión con precios incompletos daría paybacks falsos. Pon precios en la biblioteca de Equipos y recalcula.
:::

## Factura mensual — ¿qué verá el cliente?

Barras de la factura mes a mes, antes y después. El argumento comercial en una imagen: el verano casi desaparece, el invierno baja menos.

## Día tipo — ¿por qué una batería?

Consumo y producción de un día medio de invierno y de verano. El hueco entre la curva de consumo y la campana solar es exactamente lo que la batería puede desplazar. Si las dos curvas ya solapan mucho, la batería aporta poco.

# Tutorial

## Calcular y decidir

:::steps
1. Asocia un **perfil de consumo** en el paso «Datos del lugar» y calcula el dimensionamiento en **Análisis**.
2. Pulsa **Calcular ahorro** — el proyecto se guarda solo y en unos segundos aparecen los KPIs y las pestañas.
3. En **Barrido**, decide la potencia: quédate cerca del codo de la curva.
4. En **Rentabilidad**, elige la batería comparando payback y ahorro; la etiqueta «Mayor ahorro» marca la ganadora en euros, pero un payback mucho más corto puede pesar más.
5. Enseña **Factura mensual** al cliente y usa **Día tipo** para explicar el porqué de la batería.
6. Si cambias equipos o consumo, pulsa **Recalcular**.
:::

:::tip{tone=info title="La tarifa es de tu organización"}
Los precios de energía (punta/llano/valle), excedentes, potencia e impuestos se configuran por organización vía la API de tarifa; por defecto se usa una 2.0TD peninsular razonable. Los festivos aún no se modelan (cuentan como laborables).
:::

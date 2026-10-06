---
title: Análisis económico y selección de batería
routes:
  - diseno/economico
order: 34
keywords: [ahorro, factura, economia, plan, comercializadora, tarifa, payback, bateria, rentabilidad, autoconsumo, solsticio, graficas]
---

# Concepto

El paso **Análisis económico** cruza el perfil de consumo del cliente con la producción solar **hora a hora durante un año completo** y traduce el resultado a euros con el **plan eléctrico** del cliente: la factura de hoy, la factura con el sistema y lo que aporta cada equipo.

La diferencia con el dimensionado clásico está en una cifra: el **autoconsumo real**. Deja de ser el porcentaje que tú declaras en el paso 1 y pasa a ser un resultado calculado — la fracción del consumo que de verdad coincide (o se almacena) con las horas de sol de *ese* cliente.

:::cards
- **Factura sin placas** — lo que el cliente paga hoy con su plan eléctrico. Es también el techo teórico de ahorro.
- **Factura con el sistema** — mismo plan, restando autoconsumo, batería y compensación de excedentes mes a mes.
- **Aporte de la batería** — la diferencia real de factura anual entre el sistema con y sin ella. Una sola cifra, con impuestos incluidos.
:::

:::callout{tone=info}
La compensación de excedentes respeta la regla real: descuenta como máximo hasta dejar la factura del mes en cero, y el sobrante se arrastra pero nunca se cobra. Si ves el aviso de excedentes que no llegan a descontarse, ahí hay margen para más batería o menos campo.
:::

# Criterio

El paso tiene dos bloques: **Ahorro económico**, que describe la factura con el plan elegido, y **Selección de batería**, que compara alternativas.

## Plan eléctrico — ¿con qué precios?

Elige el plan de la comercializadora del cliente en el selector. Los planes se crean y editan en **Equipos › Planes eléctricos** (precios de punta, llano, valle, excedentes, potencia, impuestos y alquiler de contador). Sin plan, se usa la tarifa 2.0TD de referencia de tu organización.

## Factura mensual — ¿qué verá el cliente?

Barras de la factura mes a mes, antes y después, y debajo la **tabla de resumen** con cada mes y el total anual: sin placas, con el sistema y ahorro.

## Día tipo — ¿por qué una batería?

Consumo y producción en los **solsticios de invierno (21 de diciembre) y de verano (21 de junio)**, los dos extremos de horas de sol del año. El hueco entre la curva de consumo y la campana solar es exactamente lo que la batería puede desplazar. Si las dos curvas ya solapan mucho, la batería aporta poco.

## Selección de batería

- **Potencia fotovoltaica frente a ahorro** — ahorro anual según los kWp del campo, una curva por batería. Busca el **codo**: donde la curva se aplana, cada kWp extra aporta poco. La línea discontinua es el ahorro máximo (la factura actual).
- **Payback frente a ahorro** — cada batería es un punto: cuanto más arriba y a la izquierda, más ahorra y antes se amortiza.
- **Rentabilidad por batería** — la tabla compara factura, ahorro, aporte y payback de cada batería con el campo actual.

:::callout{tone=warning}
Las baterías sin precio unitario en el catálogo no tienen payback y quedan fuera de la gráfica (se listan debajo). Pon precios en la biblioteca de Equipos y vuelve a comparar.
:::

# Tutorial

## Calcular y decidir

:::steps
1. Asocia un **perfil de consumo** en el paso «Datos del lugar» y calcula el dimensionamiento.
2. En **Análisis económico**, elige el **Plan eléctrico del cliente**.
3. Pulsa **Calcular ahorro** — el proyecto se guarda solo y en unos segundos aparecen los KPIs, la factura mensual y la selección de batería.
4. En **Selección de batería**, decide la potencia con la primera gráfica y la batería con la de payback y la tabla de rentabilidad.
5. Enseña **Factura mensual** al cliente y usa **Día tipo** para explicar el porqué de la batería.
6. Si cambias de plan, equipos o consumo, pulsa **Recalcular**.
:::

:::tip{tone=info title="Festivos"}
Los festivos aún no se modelan en los periodos de la tarifa: cuentan como laborables.
:::

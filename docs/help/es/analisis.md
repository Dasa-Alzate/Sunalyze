---
title: Análisis y dimensionamiento
routes:
  - diseno/analisis
order: 32
keywords: [analisis, dimensionamiento, produccion, autoconsumo, pvgis, irradiancia, potencia, paneles]
---

# Concepto

El paso **Análisis** ejecuta el motor de dimensionamiento: toma las coordenadas del lugar, el panel seleccionado y la necesidad anual, consulta la base de datos de irradiancia de PVGIS-SARAH3 y devuelve el campo fotovoltaico necesario para cubrir la demanda al porcentaje de autoconsumo indicado.

El resultado incluye la potencia pico de campo, el número de módulos, la producción anual estimada y, si hay inversor fijado, la configuración de cadenas con comprobación de ventana MPP.

:::tip{tone=info title="PVGIS-SARAH3"}
Los datos de irradiancia provienen de la base de datos europea PVGIS-SARAH3, que cubre la Península, Baleares y Canarias con resolución de 5 km. El cálculo usa el ángulo óptimo para la latitud (o el ángulo coplanar si lo has definido en el paso anterior).
:::

## Métricas principales

:::cards
- **Potencia pico de campo** — suma de la potencia nominal de todos los módulos (kWp).
- **Producción anual estimada** — energía generada en un año típico (kWh), ya con pérdidas de sistema.
- **Paneles** — número de módulos necesarios para cubrir la necesidad al autoconsumo fijado.
- **Irradiancia anual** — energía solar disponible en el plano del generador (kWh/m²).
- **Ángulo óptimo** — inclinación de máxima captación para la latitud del proyecto (°).
- **Superficie necesaria** — área aproximada que ocupa el campo (m²), si el panel tiene dimensiones en catálogo.
:::

# Criterio

## Cuándo recalcular

El análisis se marca como obsoleto (triángulo naranja en el resumen lateral) cada vez que cambias coordenadas, necesidad anual, autoconsumo, panel o inversor. Pulsa **Recalcular** para actualizar.

No hace falta recalcular si solo cambias datos del cliente, cableado o disposición: esos campos no afectan al dimensionamiento.

## Inversores compatibles

Si no has fijado inversor en **Equipos**, el análisis muestra la tabla **Inversores compatibles** con todos los modelos del catálogo que encajan en la ventana MPP de la cadena calculada, ordenados por margen de tensión. Pulsa **Elegir** en la fila que prefieras — el inversor queda vinculado al proyecto para las siguientes pestañas.

# Tutorial

## Calcular el dimensionamiento

:::steps
1. Entra al paso **Análisis** desde el menú de pasos o con el botón **Continuar** en **Equipos**.
2. Si no hay resultado todavía, pulsa **Calcular dimensionamiento**.
3. Revisa las métricas: potencia pico, paneles y producción anual.
4. Si no hay inversor fijado, elige uno en la tabla **Inversores compatibles** pulsando **Elegir**.
5. Si cambias algo en pasos anteriores, pulsa **Recalcular** para actualizar los resultados.
6. Pulsa **Continuar** para pasar a **Disposición**.
:::

:::callout{tone=warning}
Si el análisis falla con un error de red o de PVGIS, comprueba que las coordenadas están dentro del área cubierta por PVGIS (Europa, África y parte de Asia). Coordenadas fuera de rango producen un error inmediato.
:::

---
title: Estudio financiero
routes:
  - finanzas
order: 70
keywords: [finanzas, van, tir, payback, capex, subvenciones, escenarios, ahorro]
---

# Concepto

El espacio de finanzas calcula la viabilidad económica de una instalación fotovoltaica: payback simple y descontado, TIR, VAN, LCOE, ROI y ahorro en CO₂, todo en función del CAPEX, la tarifa eléctrica y los supuestos de ciclo de vida que tú defines.

:::callout{tone=brand}
Esta sección requiere el flag **finance** en tu organización. Si no aparece en el menú, contacta con el administrador.
:::

:::cards
- **Estudio** — formula los supuestos y ve los resultados al instante.
- **Escenarios** — guarda, compara y carga versiones distintas del mismo análisis.
- **Estudio de ahorro** — vista de presentación al cliente con los ahorros esperados.
:::

# Criterio

## Indicadores que calcula Sunalyze

| Indicador | Descripción |
|---|---|
| Payback simple | Años sin actualización monetaria. |
| Payback descontado | Años aplicando la tasa de descuento. |
| TIR | Tasa interna de retorno del proyecto. |
| VAN | Valor actual neto a la tasa de descuento configurada. |
| LCOE | Coste nivelado de la energía generada (€/kWh). |
| ROI | Retorno sobre la inversión en la vida útil. |
| CO₂ evitado | Kg al año 1 y en toda la vida útil. |

## Subvenciones

Al activar **Incluir ayudas (mejor caso indicativo)** puedes seleccionar la comunidad autónoma y el municipio para incluir bonificaciones autonómicas y municipales (IBI + ICIO). El total es orientativo: no modela incompatibilidades ni requisitos administrativos reales.

:::callout{tone=warning}
El importe de subvenciones es un mejor caso indicativo: no sustituye a la consulta de la convocatoria oficial vigente ni garantiza la concesión.
:::

# Tutorial

## Configurar el CAPEX y los supuestos

:::steps
1. Ve a **Finanzas** — URL `/app/finanzas`.
2. Selecciona el proyecto en el desplegable de la barra superior.
3. En el campo **Modo de CAPEX** elige «Total» (un único importe) o «Desglose (equipo / mano de obra / legalización)» e introduce las cifras sin IVA.
4. Ajusta la **Tarifa eléctrica (€/kWh)**, el **Consumo anual (kWh)** y el **Precio de excedentes (€/kWh)**.
5. Revisa la sección **Supuestos del estudio**: vida útil, tasa de descuento, escalada de tarifa, degradación anual y O&M.
6. Si la instalación se financia, activa **Financiado** e introduce importe, interés y plazo.
7. Los resultados aparecen en el panel derecho en tiempo real.
:::

## Guardar y comparar escenarios

:::steps
1. Escribe un nombre en **Nombre del escenario** (p. ej. «Contado con subvenciones»).
2. Pulsa **Guardar escenario**: queda almacenado con todos los supuestos y resultados.
3. Ve a la pestaña **Escenarios** para ver la lista y comparar indicadores en paralelo.
4. Pulsa **Cargar** en un escenario para recuperar sus supuestos en el formulario del estudio.
:::

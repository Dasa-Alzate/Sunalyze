---
title: Diagrama unifilar
routes:
  - diseno/diagrama
order: 34
keywords: [diagrama, unifilar, esquema, fusibles, bateria, monofasico, trifasico, svg]
---

# Concepto

El paso **Diagrama** genera el esquema unifilar de la instalación a partir de la plantilla, los equipos del proyecto y los parámetros eléctricos que ajustes en el panel lateral. El resultado es un SVG vectorial descargable listo para adjuntar a la memoria técnica o al proyecto de legalización.

El diagrama se actualiza en vivo según escribes: no hay que pulsar ningún botón de regenerar.

:::callout{tone=info}
El diagrama unifilar requiere haber calculado el dimensionamiento primero. Si accedes al paso sin resultado de análisis, aparece un acceso directo al paso **Análisis**.
:::

## Plantillas

:::cards
- **Solar con fusibles** — cadenas CC con fusibles de cadena, seccionador CC, inversor y protecciones AC. La plantilla por defecto.
- **Solar sin fusibles** — igual pero sin fusibles de cadena; válido para instalaciones con un único string.
- **Solar con baterías** — incluye el bloque de batería y el sistema de gestión de energía.
:::

Usa los checks **Con fusibles de cadena** y **Con baterías** para alternar sin cambiar la plantilla a mano.

# Tutorial

## Generar y descargar el esquema

:::steps
1. Entra al paso **Diagrama**; la plantilla se preselecciona según los equipos del proyecto (con o sin batería).
2. Selecciona la **Plantilla** en el desplegable si quieres cambiarla.
3. Ajusta los parámetros del bloque **Campo fotovoltaico (CC)**: **Modelo de panel**, **Voc del panel**, **Isc del panel**, **Paneles por cadena**, **Nº de cadenas**, **Fusible CC**, **Tensión del seccionador CC** y **Sección de cable CC**.
4. Ajusta los parámetros del bloque **Salida e inversor (CA)**: **Modelo de inversor**, **Potencia del inversor**, **Corriente de salida**, **Fases** (Monofásico / Trifásico), **Magnetotérmico**, **Diferencial**, **Sensibilidad diferencial** y **Sección de cable CA**.
5. Revisa la **Vista previa en vivo** a la derecha: se actualiza con cada cambio.
6. Pulsa **Descargar SVG** para guardar el esquema vectorial.
:::

:::tip{tone=success}
Los campos **Modelo de panel**, **Voc**, **Isc**, **Modelo de inversor** y **Potencia del inversor** se rellenan automáticamente con los datos de los equipos vinculados al proyecto. Puedes sobreescribirlos si necesitas ajustar algún valor para el esquema.
:::

:::tip{tone=info title="Desde cualquier paso"}
El botón **Diagrama unifilar** de la barra superior abre directamente este paso sin pasar por los anteriores, útil si solo quieres ajustar o descargar el esquema.
:::

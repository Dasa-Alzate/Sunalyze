---
title: Legalización por comunidad autónoma
routes:
  - legalizacion
order: 75
keywords: [legalizacion, ccaa, expediente, mtd, tramitacion, autoconsumo, comunidad autonoma]
---

# Concepto

El panel de legalización centraliza la tramitación administrativa de una instalación fotovoltaica: estado del expediente, guía de trámites específica por comunidad autónoma, asistente de presentación y generación del modelo oficial de MTD cuando la CCAA lo permite.

## Flujo de estados

El expediente avanza por cinco estados:

:::flow
- **Borrador** — documentación en preparación, aún sin presentar.
- **En revisión** — tramitación interna antes de presentar ante Industria.
- **Presentado** — expediente registrado en la sede electrónica de la CCAA.
- **Aprobado** — inscripción en el registro confirmada.
- **Rechazado** — presentación denegada; corrige y vuelve a borrador.
:::

# Criterio

:::norm{code="RD 244/2019"}
El Real Decreto 244/2019 regula las condiciones administrativas, técnicas y económicas del autoconsumo de energía eléctrica. Establece los procedimientos simplificados para instalaciones de hasta 100 kW en baja tensión y la inscripción en el registro autonómico de autoconsumo. La tramitación concreta la ejecuta cada CCAA en su sede electrónica.
:::

:::tip{tone=info title="17 CCAA disponibles"}
El selector admite las diecisiete comunidades autónomas. Si el proyecto tiene coordenadas guardadas, Sunalyze detecta la CCAA automáticamente mediante geocodificación inversa (OpenStreetMap Nominatim) y la muestra con un aviso.
:::

# Tutorial

## Asignar la comunidad autónoma y ver la guía

:::steps
1. Abre un proyecto y navega a **Legalización** desde el menú o el listado de proyectos.
2. En la tarjeta **Comunidad autónoma**, abre el desplegable **Dónde se tramita la instalación** y elige la CCAA — o espera a que Sunalyze la detecte si el proyecto tiene coordenadas.
3. Si existe guía para esa CCAA, aparecen la plataforma de tramitación, los pasos de presentación y los procedimientos y modelos oficiales con sus enlaces directos.
4. Los modelos marcados con **Generable desde Sunalyze** se pueden descargar con el botón **MTD modelo oficial** de la barra superior.
:::

## Registrar el expediente y avanzar el estado

:::steps
1. En la tarjeta **Estado del expediente**, pulsa el botón de transición que corresponda: **Enviar a revisión**, **Marcar como presentado**, **Marcar como aprobado** o **Marcar como rechazado**.
2. Una vez presentado ante Industria, copia el número de expediente en el campo **Nº de expediente de Industria** e indica la **Fecha de presentación**.
3. Pulsa **Guardar expediente** para registrarlo en el proyecto.
:::

## Usar el asistente de presentación

Cuando la CCAA dispone de asistente, aparece la tarjeta **Asistente de presentación** con los datos del proyecto en el orden exacto que pide el formulario de la sede electrónica.

:::steps
1. Abre la sede electrónica de la CCAA en otra pestaña del navegador.
2. Para cada campo del formulario, busca el dato correspondiente en el asistente y pulsa el icono de copiar para copiarlo al portapapeles.
3. Pégalo en el formulario de la sede. La firma y el envío los realizas tú con tu certificado digital.
:::

:::callout{tone=info}
Si tu rol no incluye el permiso **project:legalize**, los botones de transición y el campo de expediente están deshabilitados. Pide al administrador que ajuste tu rol si necesitas cambiar el estado.
:::

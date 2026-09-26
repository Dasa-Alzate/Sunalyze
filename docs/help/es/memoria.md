---
title: Memoria técnica
routes:
  - memoria
order: 55
keywords: [memoria, pdf, memoria tecnica, protecciones, presupuesto, generar, firma]
---

# Concepto

La vista de Memoria técnica reúne todos los datos necesarios para producir el documento PDF que se entrega con la instalación: datos del cliente, contrato eléctrico, configuración del sistema, protecciones y presupuesto. A la derecha se actualiza en tiempo real una **Vista previa del documento** que refleja cada cambio que haces en los campos.

## Secciones del formulario

:::cards
- **Cliente y emplazamiento** — nombre del cliente, localidad, dirección, código postal y referencia catastral.
- **Contrato eléctrico** — compañía, CUPS, potencia contratada, tensión, tipo de voltaje y objetivo del sistema (con o sin inyección de excedentes).
- **Configuración** — potencia pico (kWp), número de paneles, entradas MPPT, ubicación de paneles y disposición, y ubicación del inversor.
- **Protecciones** — magnetotérmico DC (tensión máxima y amperaje), magnetotérmico AC, diferencial AC, protector de sobretensiones y longitud del cable de tierra.
- **Presupuesto** — editor de partidas presupuestarias, disponible cuando la memoria se abre desde un proyecto guardado.
:::

Cada sección tiene un indicador de estado: verde si todos los campos obligatorios están rellenos, ámbar si faltan algunos y gris si está sin tocar.

# Tutorial

## Rellenar y previsualizar

:::steps
1. Abre la memoria desde un proyecto (botón **Memoria** en el paso de diseño) o accede a `/app/memoria` para un borrador libre.
2. Expande la sección **Cliente y emplazamiento** haciendo clic en su cabecera; rellena los campos obligatorios.
3. Continúa con **Contrato eléctrico**, **Configuración** y **Protecciones**. La vista previa de la derecha se actualiza automáticamente.
4. Si abres la memoria desde un proyecto, muchos campos se rellenan solos con los datos del diseño.
:::

:::tip{tone=info title="Guardar sin generar el PDF"}
Pulsa **Guardar** para persistir los datos en el proyecto sin cambiar su estado. Útil para cerrar sesión y retomar más tarde.
:::

## Generar el PDF

:::steps
1. Asegúrate de que todos los indicadores de sección están en verde (no hay pendientes).
2. Pulsa **Generar PDF** — el sistema valida los campos y, si todo está correcto, genera el documento y lo abre en una pestaña nueva.
3. Si faltan campos obligatorios, aparece un aviso con los primeros que faltan y la sección correspondiente se expande para que los veas.
4. Al generar desde un proyecto, el estado del proyecto cambia automáticamente a «Memoria».
:::

:::callout{tone=warning}
Solo los usuarios con el permiso **Firmar memoria** pueden generar el PDF. Si el botón **Generar PDF** está desactivado, contacta con el administrador de tu workspace para que te asigne el rol adecuado.
:::

## Añadir el presupuesto

:::steps
1. La sección **Presupuesto** solo aparece cuando la memoria está asociada a un proyecto guardado.
2. Expándela y usa el editor de partidas para ajustar materiales, mano de obra e impuestos.
3. Pulsa **Guardar** en el editor de presupuesto; la vista previa se actualiza con el nuevo importe.
:::

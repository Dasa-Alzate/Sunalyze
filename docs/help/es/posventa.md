---
title: Seguimiento de instalaciones (Posventa)
routes:
  - posventa
order: 80
keywords: [posventa, instalaciones, mantenimiento, incidencias, rendimiento, visitas, garantía]
---

# Concepto

Posventa es el módulo de seguimiento post-instalación. Cada instalación nace de un proyecto aprobado y agrupa en un solo lugar el historial de mantenimiento, las incidencias abiertas y las lecturas reales de producción.

:::cards
- **Operativa** — instalación sin alertas activas.
- **Incidencia** — existe al menos una incidencia abierta o en proceso.
- **Mantenimiento** — visita de mantenimiento próxima o en curso.
- **Baja** — instalación fuera de servicio o dada de baja.
:::

:::tip{tone=info title="Feature flag"}
Posventa puede estar desactivado en tu organización. Si no ves la sección en el menú lateral, pide a tu administrador de plataforma que lo active en **Configuración → Flags**.
:::

# Tutorial

## Crear una instalación

:::steps
1. Abre **Posventa** en el menú lateral.
2. Pulsa **Convertir en instalación**.
3. En el diálogo, elige el **Proyecto aprobado** que quieres activar y pulsa **Crear instalación**.
4. La instalación aparece en el listado con el estado **Operativa** por defecto.
:::

## Gestionar mantenimiento

:::steps
1. Abre una instalación de la lista.
2. Ve a la pestaña **Mantenimiento** para ver las visitas programadas.
3. Usa el formulario de nueva visita para registrar tipo (**Preventivo** / **Correctivo**), fecha y notas.
4. Cambia el estado de cada visita a **Realizada** o **Cancelada** cuando proceda.
:::

## Registrar incidencias

:::steps
1. En el detalle de la instalación, ve a la pestaña **Incidencias**.
2. Crea una nueva incidencia con su gravedad: **Baja**, **Media**, **Alta** o **Crítica**.
3. Actualiza el estado a **En proceso** o **Resuelta** a medida que avance la resolución.
4. El estado global de la instalación cambia automáticamente a **Incidencia** mientras haya alguna abierta.
:::

## Consultar el rendimiento

:::steps
1. Ve a la pestaña **Rendimiento** de la instalación.
2. Pulsa **Añadir lectura** para registrar la producción real acumulada.
3. El gauge muestra el ratio real/esperado: verde ≥ 90 %, ámbar ≥ 70 %, rojo por debajo.
4. El valor esperado procede del análisis del proyecto convertido.
:::

:::callout{tone=warning}
Las lecturas son manuales. Para un seguimiento fiable a largo plazo conecta un datalogger o la API del inversor.
:::

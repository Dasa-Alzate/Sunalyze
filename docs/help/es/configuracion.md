---
title: Configuración del estudio
routes:
  - configuracion
  - configuracion/marca
  - configuracion/presupuesto
  - configuracion/flags
order: 95
keywords: [configuracion, marca, logo, presupuesto, flags, color, tarifa, organización]
---

# Concepto

La sección **Configuración** agrupa los ajustes de toda la organización: la identidad visual que se aplica a los documentos generados, los parámetros económicos que alimentan los presupuestos y los feature flags que controlan qué módulos están activos.

:::cards
- **Marca** — logo, color principal, prefijo de nº de serie y pie de página de documentos.
- **Presupuesto** — tarifas de mano de obra, inflación de equipos y partidas personalizadas.
- **Flags** — activación de módulos y funciones experimentales (solo administradores de plataforma).
:::

:::tip{tone=info title="Acceso"}
Las pestañas **Marca** y **Presupuesto** requieren el permiso **org:manage**. La pestaña **Flags** solo es visible para administradores de plataforma.
:::

# Tutorial

## Marca

:::steps
1. Ve a **Configuración** y selecciona la pestaña **Marca**.
2. Pulsa **Subir logo** (o **Reemplazar logo**) para subir un PNG, JPEG, WebP o SVG de hasta 2 MB.
3. Elige el **Color principal** con el selector o introduce el valor hexadecimal en el campo de texto.
4. Escribe el **Prefijo de nº de serie** (hasta 8 caracteres) para que tus proyectos se numeren como PREFIJO-0001.
5. Rellena el **Texto del pie de página** que aparecerá en los documentos generados.
6. Pulsa **Guardar marca** para aplicar los cambios.
:::

## Presupuesto

:::steps
1. Selecciona la pestaña **Presupuesto**.
2. Introduce el **Fijo por instalación (€)**: importe de puesta en marcha y gestión que se suma una sola vez por proyecto.
3. Introduce el **Por módulo instalado (€/ud)**: se multiplica por el número de módulos del diseño.
4. Ajusta la **Inflación general de equipos (%)**: cubre la fluctuación de precios; se compone con la inflación propia de cada equipo sin aparecer como concepto separado.
5. Añade **partidas personalizadas** con **Añadir partida**: elige capítulo, descripción, unidad, cantidad y precio unitario.
6. Pulsa **Guardar parámetros** cuando hayas terminado.
:::

:::callout{tone=info}
Las partidas personalizadas se incluyen en cada presupuesto pre-generado. Las filas sin descripción se ignoran al guardar.
:::

## Flags

:::steps
1. Selecciona la pestaña **Flags** (visible solo para administradores de plataforma).
2. La tabla muestra todos los feature flags con su valor por defecto y el override global activo.
3. Activa o desactiva el override global de cada flag según necesites.
4. Para volver al valor por defecto, limpia el override del flag.
:::

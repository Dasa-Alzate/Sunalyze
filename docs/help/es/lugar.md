---
title: Ubicación del proyecto
routes:
  - diseno
  - diseno/lugar
order: 30
keywords: [lugar, coordenadas, latitud, longitud, consumo, cliente, necesidad, coplanar]
---

# Concepto

El paso «Datos del lugar» ancla el proyecto al territorio: establece quién es el cliente, dónde está la instalación y cuánta energía necesita. Con esos tres datos —coordenadas, necesidad anual y porcentaje de autoconsumo— el motor de cálculo puede consultar la irradiancia real de PVGIS y dimensionar el campo fotovoltaico.

## Datos del cliente

El bloque **Cliente** identifica el proyecto en el listado y en la cabecera de la memoria técnica.

:::cards
- **Cliente / proyecto** — nombre o razón social; aparece en la topbar y en el PDF. Campo obligatorio.
- **Localidad** — municipio; se rellena solo si usas el mapa para fijar las coordenadas.
- **Dirección** — calle y número; pasa directamente a la sección «Cliente y emplazamiento» de la memoria.
:::

## Emplazamiento y consumo

:::cards
- **Latitud / Longitud** — coordenadas decimales (ej. 38.352 / −0.493). Obligatorias para consultar PVGIS.
- **Necesidad anual** — consumo que quieres cubrir, en kWh/año. Obligatorio para dimensionar.
- **Autoconsumo** — porcentaje del consumo a cubrir con solar (70 %, 80 %, 90 % o 100 %).
:::

:::tip{tone=info title="Mapa interactivo"}
Si el flag **geo_map** está activo en tu cuenta, aparece un mapa debajo del formulario. Haz clic en cualquier punto para fijar latitud y longitud automáticamente; la **Localidad** también se rellena con el topónimo más cercano.
:::

## Instalación coplanar

Marca **Instalación coplanar (definir inclinación y azimut)** cuando los módulos van sobre teja o cubierta con ángulo fijo. Al activarlo aparecen dos campos adicionales:

:::cards
- **Inclinación (°)** — ángulo del plano respecto a la horizontal (0–90°).
- **Azimut (°)** — orientación del plano; 180° = sur exacto.
:::

Si no marcas coplanar, el paso de análisis calcula automáticamente el ángulo óptimo para tu latitud.

# Tutorial

## Rellenar los datos del lugar

:::steps
1. Escribe el nombre en **Cliente / proyecto** — es el único campo estrictamente obligatorio para guardar.
2. Rellena **Necesidad anual** (kWh/año) con el consumo real o estimado del cliente.
3. Ajusta **Autoconsumo** al porcentaje que quieres cubrir con solar.
4. Introduce **Latitud** y **Longitud** o usa el mapa para fijar el punto con un clic.
5. Si la cubierta tiene inclinación fija, activa **Instalación coplanar** e introduce inclinación y azimut.
6. Pulsa **Continuar** — el wizard valida los campos obligatorios antes de pasar al paso siguiente.
:::

:::callout{tone=warning}
Si cambias las coordenadas o la necesidad anual después de haber calculado, el resumen lateral muestra un aviso «Entradas cambiadas — recalcula para actualizar». Vuelve al paso **Análisis** y pulsa **Recalcular**.
:::

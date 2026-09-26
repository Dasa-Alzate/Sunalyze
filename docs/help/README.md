# Centro de ayuda — guía de autoría

Los artículos de ayuda viven en este directorio como Markdown y viajan compilados dentro del bundle del frontend. No hay CMS ni base de datos: editar la ayuda es editar un fichero, abrir un PR y ya.

## Estructura

```
docs/help/
├── es/<slug>.md        idioma base (fuente de verdad)
├── en/<slug>.md        espejo por idioma (mismo slug)
├── screenshots/        PNGs referenciados por los artículos
├── screens.json        manifest de captura automática (opcional)
└── surfaces.json       vocabulario de vistas y subvistas válidas
```

El slug es el nombre del fichero y debe coincidir entre idiomas.

## Comandos

| Comando | Qué hace |
| --- | --- |
| `npm run help:build` | Compila los artículos al artefacto JSON. Falla con `fichero:línea` si algo no valida. |
| `npm run help:check` | Igual, pero también falla si hay warnings (para CI). |
| `npm run help:stamp` | Sella las traducciones EN con el hash del original ES. |
| `npm run help:shots` | Captura pantallas con Playwright según `screens.json`. |

En desarrollo no hace falta nada: el plugin de Vite recompila y recarga al guardar cualquier fichero de `docs/help/`.

## Frontmatter

```yaml
---
title: Disposición de módulos
routes:
  - diseno/disposicion
order: 40
keywords: [disposicion, zonas, strings]
---
```

| Campo | Obligatorio | Descripción |
| --- | --- | --- |
| `title` | sí | Título visible del artículo. |
| `routes` | no | Superficies donde el artículo aparece como ayuda contextual: `vista` o `vista/subvista`, validadas contra `surfaces.json`. |
| `order` | no | Entero para desempatar cuando varias rutas coinciden (gana el menor; por defecto 100). |
| `keywords` | no | Términos extra para el buscador. |
| `status` | no | `published` (por defecto) o `draft` (se compila pero no se publica). |
| `source_hash` | solo EN | Lo escribe `help:stamp`; no lo edites a mano. |

## Pestañas

Cada H1 abre una pestaña. Solo existen cuatro, en este orden canónico, y todas son opcionales (mínimo una):

```markdown
# Concepto     ← qué es y por qué existe
# Criterio     ← reglas, normativa, decisiones de diseño
# Flujo        ← el recorrido de principio a fin, a vista de pájaro
# Tutorial     ← pasos concretos con nombres de botones reales
```

Dentro de una pestaña: los H2 crean títulos de sección y el resto es prosa Markdown normal (negritas, enlaces, tablas GFM, código).

## Directivas

Los bloques especiales usan la sintaxis `:::tipo{attrs}` cerrada con `:::`:

```markdown
:::tip{tone=info title="Cubiertas a varias aguas"}
Crea una zona por agua con «Añadir zona».
:::
```

| Directiva | Atributos | Cuerpo |
| --- | --- | --- |
| `tip` | `tone`, `title` | Markdown. Nota destacada con icono de bombilla. |
| `callout` | `tone` | Markdown. Aviso en banda. |
| `steps` | — | Lista: pasos numerados de tutorial. |
| `cards` | — | Lista: tarjetas de definición. |
| `flow` | — | Lista: línea de tiempo vertical. |
| `norm` | `code` | Markdown. Referencia normativa (`code` = etiqueta, p. ej. `"IDAE PCT-C-REV"`). |
| `screenshot` | `src`, `alt` | Markdown opcional como pie de foto. `src` relativo a `screenshots/`. |

Tonos válidos: `info`, `success`, `warning`, `danger`, `brand`, `purple`.

En las directivas de lista (`steps`, `cards`, `flow`) cada ítem puede llevar título con el patrón `**Título** — cuerpo`:

```markdown
:::cards
- **Zona** — polígono de cubierta con plano propio.
- **Obstáculos** — elementos con altura que proyectan sombra.
:::
```

## Traducciones

El español es la fuente de verdad. El flujo para EN:

1. Edita `es/<slug>.md`.
2. Traduce (o actualiza) `en/<slug>.md`.
3. `npm run help:stamp` — sella el EN con el hash del ES actual.

Si el ES cambia y el EN no se vuelve a sellar, el build lo marca como obsoleto y la app enseña el artículo ES con un aviso: nunca se muestra un inglés desactualizado.

## Capturas de pantalla

Los artículos referencian PNGs por nombre (`src=vista/nombre.png`). Dos maneras de producirlos:

- **Automática**: declara la captura en `screens.json` y corre `npm run help:shots` con la app levantada (`HELP_SHOTS_EMAIL`, `HELP_SHOTS_PASSWORD` y las variables que use el manifest). Ver el propio manifest como ejemplo.
- **Manual**: suelta el PNG en `screenshots/` con el nombre referenciado. Borrar `screens.json` desactiva la vía automática sin tocar ningún artículo.

Si un PNG referenciado no existe, el build avisa (no falla) y la app simplemente no muestra la figura.

## Validación

El build rechaza con mensaje `fichero:línea`: rutas fuera de `surfaces.json`, pestañas o directivas desconocidas, tonos inválidos, directivas sin cerrar, contenido antes de la primera pestaña. Avisa (sin fallar) de: capturas ausentes, traducciones obsoletas, superficies cubiertas por varios artículos y superficies sin artículo.

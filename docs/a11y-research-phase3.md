# Accesibilidad — Fase 3: Percepción / preferencias + tests + documentación

Tercera y última fase de la expansión de accesibilidad del frontend React + Vite. Las fases 1
y 2 cubrieron semántica, foco, labels, `sr-only`, lint `jsx-a11y`, focus trap, menús por
teclado, `:focus-visible` y live regions. Esta fase cubre **percepción** (WCAG 1.4.x) y
preferencias del usuario, más tests automáticos con axe-core y una guía de patrones.

## Criterios WCAG 2.1 relevantes a esta fase

### 1.4.3 Contrast (Minimum) (AA)
Texto normal ≥ 4.5:1, texto grande (≥ 24px o ≥ 18.66px bold) y componentes de UI ≥ 3:1
respecto a su fondo. El ratio se calcula con la luminancia relativa: se linealiza cada canal
sRGB (`v/12.92` si `v ≤ 0.03928`, si no `((v+0.055)/1.055)^2.4`), se pondera
`0.2126·R + 0.7152·G + 0.0722·B`, y el contraste es `(L1+0.05)/(L2+0.05)`.

### 1.4.4 Resize Text (AA)
El texto debe poder ampliarse al 200% sin pérdida de contenido ni de funcionalidad. Se logra
con unidades relativas (`rem`/`em`) en tipografía y espaciado, evitando alturas fijas en `px`
que recorten texto.

### 1.4.10 Reflow (AA)
El contenido se adapta a 320px CSS de ancho (equivalente a zoom 400% en 1280px) sin scroll en
dos ejes. Los grids multi-columna deben colapsar a una sola columna en breakpoints estrechos.

### 1.4.11 Non-text Contrast (AA)
Los componentes de UI y los límites de estado (bordes de input, foco, controles) necesitan
≥ 3:1. La decoración pura (líneas separadoras, sombras) está exenta.

### 1.4.12 Text Spacing (AA)
El layout aguanta el aumento de interlineado/espaciado entre letras y palabras. `line-height`
relativo (ya en tokens) y ausencia de alturas de línea fijas en `px` lo facilitan.

### 2.3.3 Animation from Interactions (AAA) + 2.2.2 / `prefers-reduced-motion`
Las animaciones disparadas por interacción o decorativas deben poder desactivarse. Se respeta
`@media (prefers-reduced-motion: reduce)` desactivando o reduciendo a un cambio instantáneo
toda transición/animación, incluido el "black sweep" de transición de página.

### 2.5.5 / 2.5.8 Target Size
Los objetivos táctiles deberían medir ≥ 24px (AA, 2.5.8) e idealmente ≥ 44px (AAA, 2.5.5).

### `prefers-contrast: more` y `color-scheme`
No es un criterio numerado, pero refuerza 1.4.3/1.4.11: en modo alto contraste se endurecen
bordes y se oscurece el texto sutil. `color-scheme: light` declara el esquema para que los
controles nativos (scrollbars, inputs) se rendericen coherentes.

## Auditoría de contraste de tokens (1.4.3 / 1.4.11)

Ratios reales calculados sobre los tokens de `styles/tokens.css` contra sus fondos de uso.
La inmensa mayoría ya cumplían; solo se ajustó lo que fallaba, con el mínimo cambio.

| Combinación (texto / fondo) | Antes | Después | Estado |
| --- | --- | --- | --- |
| `--text-body` (ink-700) / cream, white | 9.56 / 10.05 | sin cambio | PASS |
| `--text-muted` (ink-600) / white, cream, ink-100 | 6.19 / 5.89 / 5.54 | sin cambio | PASS |
| `--text-strong` (ink-900) / white | 15.52 | sin cambio | PASS |
| `--text-link` (blue-500) / white, cream | 5.38 / 5.12 | sin cambio | PASS |
| `--text-brand` (green-700) / white | 8.33 | sin cambio | PASS |
| `--primary-fg` white / primary (green-500) — botón | 5.27 | sin cambio | PASS |
| `--accent-fg` / accent (amber-500) — botón | 5.27 | sin cambio | PASS |
| badge-brand green-800 / green-100 | 8.31 | sin cambio | PASS |
| badge-accent amber-700 / amber-100 | 4.79 | sin cambio | PASS |
| `--warning-fg` (amber-700) / amber-50 | 5.33 | sin cambio | PASS |
| `--danger-fg` / red-50, `--info-fg` / blue-50, `--success-fg` / green-50 | 9.03 / 10.68 / 9.47 | sin cambio | PASS |
| `--border-strong` (ink-500) / white (borde input, UI 3:1) | 3.53 | sin cambio | PASS |
| **`--text-subtle` (ink-500 #8a8886) / white** | **3.53** | **5.22** | **AJUSTADO → PASS** |
| `--text-subtle` / cream, ink-100, green-50 | 3.36 / 3.30 / 3.27 | 4.97 / 4.67 / 4.64 | AJUSTADO → PASS |

### Único token ajustado

- **`--text-subtle`**: antes apuntaba a `--ink-500` (`#8a8886`), que como **color de texto**
  daba 3.53:1 sobre blanco (FALLA 1.4.3). Se redefine a un gris más oscuro **`#6e6c6b`**
  (5.22:1 sobre blanco, ≥ 4.5:1 sobre cream, ink-100 y green-50). Se mantiene `--ink-500`
  intacto porque también alimenta `--border-strong` (uso decorativo/UI, donde 3.53:1 ya supera
  el umbral 3:1 de 1.4.11). Así el cambio afecta solo al texto sutil (eyebrows, metadatos,
  placeholders, hints secundarios) y no a los bordes.
- **NOTA PARA REVISIÓN HUMANA:** este cambio es **visualmente apreciable** — todo el texto
  "subtle" (etiquetas eyebrow en mayúsculas, metadatos de tabla, captions) se ve más oscuro.
  Es el comportamiento correcto para AA, pero conviene una validación visual.

### No-ajustados por ser decoración / no-texto (exentos de 1.4.3)

- `--border` (ink-300, 1.53:1 sobre blanco) y `--state-warn` (amber-500, 2.60:1): son líneas y
  puntos de estado decorativos; el estado nunca se transmite solo por color (hay icono/texto).
- `--state-warn` como **borde** de `.sun-step--stale`/`.sun-msection--active` acompaña a texto
  e icono, por lo que el color no es portador único de información.

## Cobertura `prefers-reduced-motion`

Antes existía en 4 sitios (`web.css` reveal/hero block, `Landing.jsx`, `HeroPreview.jsx`,
`TransitionProvider.jsx` que ya salta el sweep por JS). Se completa para que **toda**
animación/transición de la app respete la preferencia mediante un bloque global "catch-all"
(`*` con `animation`/`transition` reducidas a `0.01ms` y `scroll-behavior: auto`) más reglas
específicas para el black-sweep (`transition.css`) y los keyframes de `app.css`/`kit.css`.

## Reflow / zoom (1.4.10 / 1.4.4)

El shell y las vistas ya usan grids que colapsan (`app.css` a 1100px, `web.css` a 920px) y
tipografía/espaciado en `rem` vía tokens. Se añade un breakpoint estrecho que colapsa el shell
`grid-template-columns` a una sola columna (la barra lateral deja de ser fija) para soportar
320px CSS / zoom 400% sin scroll horizontal.

## Tests axe-core (D2)

Runner: **vitest** + **jsdom** + **vitest-axe** (matcher `toHaveNoViolations`). Cada test
renderiza un componente o vista clave con `@testing-library/react`, ejecuta `axe()` sobre el
contenedor y asevera cero violaciones. Cubre las primitivas accesibles del design system
(`Field`, `SelectField`, `Btn`, `IconBtn`, `Scrim`, `Badge`, `Metric`) y composiciones de
formulario/diálogo representativas de las vistas.

## Doc de patrones (D3)

`docs/a11y-patterns.md`: guía operativa de cómo construir componentes accesibles en este
repo (diálogos con `Scrim`/`useFocusTrap`, formularios con `Field`, feedback con live regions,
`:focus-visible`, `sr-only`, route announcer, y los comandos `npm run lint` / `npm test`).

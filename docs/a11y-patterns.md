# Guía de patrones de accesibilidad (frontend Sunalyze)

Cómo construir un componente accesible en este proyecto. Reutiliza siempre las primitivas del
design system (`src/shared/ui/index.jsx`) y los tokens (`src/styles/tokens.css`) antes de
escribir markup nuevo: ya incorporan semántica, foco y contraste correctos.

## Formularios — usa `Field` y `SelectField`

`Field` asocia `<label htmlFor>` con el control por `id`, genera `aria-describedby` para hint y
error, y marca `aria-invalid` / `aria-required`. **No** escribas `<input>` sueltos.

```jsx
<Field id="potencia" label="Potencia pico" hint="kWp" required
       error={errores.potencia} numeric />
<SelectField id="tipo" label="Tipo" options={[{ value: 'res', label: 'Residencial' }]} />
```

- Pasa siempre un `id` estable y un `label` descriptivo (2.4.6, 3.3.2).
- El error va en `error=` (texto, no solo color): se asocia por `aria-describedby` (3.3.1).
- Agrupa controles relacionados en `<fieldset>` + `<legend>`.

## Diálogos / drawers — usa `Scrim` + `useFocusTrap`

`Scrim` aplica `role="dialog"`, `aria-modal`, cierre con `Escape`, backdrop como `<button>` con
`aria-label`, y atrapa el foco con `useFocusTrap`. Pon el contenido dentro y dale un `<h3>` de
título que coincida con `label`.

```jsx
{open && (
  <Scrim label="Editar proyecto" onClose={() => setOpen(false)}>
    <div className="sun-drawer">
      <header className="sun-drawer__head"><h3>Editar proyecto</h3></header>
      <div className="sun-drawer__body">{/* campos */}</div>
    </div>
  </Scrim>
)}
```

## Botones e iconos — `Btn` / `IconBtn`

- Toda acción es un `<button>` (nunca `div`/`span` con `onClick`): foco y teclado nativos (2.1.1).
- `IconBtn` **exige** `label` (se usa como `aria-label` + `title`) porque no tiene texto visible
  (4.1.2). No omitas el `label`.
- Objetivos táctiles: los botones miden ≥ 24px; respétalo si creas controles icon-only nuevos.

## Menús por teclado — patrón `ExportMenu`

Los menús emergentes exponen `aria-haspopup`, `aria-expanded`, `aria-controls`, `role="menu"` /
`role="menuitem"`, navegación con flechas/Home/End, cierre con `Escape` y devolución de foco al
disparador. Replica ese patrón para cualquier popover de acciones.

## Feedback / estados — live regions

- Cambios de estado que no reciben foco se anuncian con una región `aria-live="polite"`
  (4.1.3). Los toasts y el route announcer del shell ya lo hacen.
- La navegación SPA mueve el foco a `<main id="main" tabindex="-1">` y anuncia la ruta.
- No transmitas estado solo por color: acompaña con icono y/o texto (1.4.1). `Dot`/`Badge`
  van siempre con etiqueta.

## Foco visible — `:focus-visible`

El foco de teclado usa el token `--shadow-focus` (o `outline` global en `tokens.css`). No
elimines el outline sin sustituirlo (2.4.7). Usa `:focus-visible`, no `:focus`, para no mostrar
el anillo en clics de ratón.

## Texto solo para lectores — `.sr-only`

Para etiquetas accesibles sin presencia visual usa la clase `.sr-only` (visually-hidden, no
`display:none`). El skip-link se vuelve visible al recibir foco.

## Movimiento y preferencias

- Toda animación/transición respeta `@media (prefers-reduced-motion: reduce)` (bloque global en
  `tokens.css` + reglas específicas en `transition.css`). Si añades una animación nueva, no
  necesitas reglas extra salvo casos especiales: el catch-all global ya la neutraliza.
- `tokens.css` declara `color-scheme: light` y un bloque `@media (prefers-contrast: more)` que
  endurece bordes y oscurece texto. Apóyate en los tokens (`--text-*`, `--border-*`) y heredarás
  ese soporte.

## Contraste (1.4.3 / 1.4.11)

- Texto normal ≥ 4.5:1, texto grande / UI ≥ 3:1. Usa los tokens de texto (`--text-body`,
  `--text-muted`, `--text-subtle`, `--text-strong`); todos pasan AA sobre los fondos del sistema.
- Si introduces un par color/fondo nuevo, calcula el ratio antes de fijarlo (ver
  `docs/a11y-research-phase3.md` para la fórmula y la auditoría de tokens).

## Reflow / zoom (1.4.10 / 1.4.4)

- Usa unidades relativas (`rem`/tokens de espaciado), no `px` fijos en tipografía.
- Los grids deben colapsar a una columna en pantallas estrechas (ver breakpoints en `app.css` y
  `web.css`); verifica el zoom al 200–400% sin scroll horizontal.

## Verificación

Antes de dar por terminado un cambio de UI, ejecuta desde `frontend/`:

```bash
npm run lint   # eslint + jsx-a11y
npm test       # tests axe-core (vitest + jsdom + vitest-axe)
npm run build  # build de producción
```

Los tests axe viven en `src/test/a11y.test.jsx`: renderizan las primitivas y composiciones
clave y aseveran cero violaciones. Añade un caso cuando crees un componente accesible nuevo.

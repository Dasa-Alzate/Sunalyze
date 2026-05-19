# Power-user layer — research & analysis (Fase A)

## Scope
Fase A: action registry + cross-platform shortcut engine + command palette + shortcut sheet.
Fase B (CLI console) is out of scope.

## Hard user constraints
- Only modifier+key combos. No Vim-style chords (`g` then `d`), no `:` mode, no bare-key
  bindings (no lone `?` or `/`). Every shortcut carries at least one modifier.
- Cross-platform Windows / Linux / Mac.

## Cross-platform shortcut matching (critical)
- **Normalized "Mod"**: `metaKey` on Mac (⌘), `ctrlKey` on Windows/Linux. Platform detected
  once via `navigator.platform` / `userAgent` (Mac if `/Mac|iP(hone|ad|od)/`).
- **Match by `event.code`** (physical key: `KeyD`, `KeyK`, `Slash`), never by `event.key`.
  Reason: on Mac, Opt/Alt+D produces the glyph `∂` in `event.key`, and `event.key` is also
  layout-dependent. `event.code` is the physical position, so `Alt`/`Opt`+letter fires
  regardless of layout or the dead-key glyph.
- **`preventDefault()` only when a combo is one of ours** (matched in the registry). Never
  swallow keys we don't own.

### Browser collisions (documented)
- `Alt+D` focuses the address bar in many Windows/Linux browsers (Chrome/Firefox/Edge). When
  the app has focus our handler calls `preventDefault()`, but if focus is in the browser
  chrome the browser wins. Acceptable: our binding is best-effort inside the document.
- `Ctrl+K` focuses the address bar / search in some browsers (Firefox). We `preventDefault()`
  when the document has focus so the palette opens.
- `Mod+/` is generally free. On some keyboard layouts `Slash` needs Shift; we match the
  physical `Slash` code with Mod, ignoring Shift state for the sheet so it is reachable.
- `Alt+letter` may trigger menu mnemonics on Windows; we `preventDefault()` to suppress when
  the combo is ours and focus is in the document.

## Existing patterns to reuse (no new paradigm)
- Router: `react-router-dom` v6 `createBrowserRouter`. Navigation in-app goes through the
  Transition service `useTransition().navigate(to)` (animated, respects reduced-motion).
  The registry actions receive a `ctx` with `navigate` so they stay framework-thin.
- Overlays: `useFocusTrap(active)` (focus trap + inert siblings + focus restore on unmount)
  and the `Scrim` pattern (`role="dialog"`, `aria-modal`, Escape closes). Palette uses a
  centered variant of the scrim; both reuse `useFocusTrap` and restore focus.
- UI: `Icon`, design tokens in `src/styles/tokens.css`, `.kbd` styling already exists.
- Providers mount in `RootLayout` (AuthProvider > TransitionProvider > Outlet + ToastHost).
  The power-user provider mounts inside TransitionProvider (needs `navigate`) and only inside
  the authenticated `/app` area is where most actions apply, but the engine is global.

## No theme toggle exists
The codebase has no dark-mode / `data-theme` system. The prompt says "toggle theme (si
existe)" — it does not, so that action is omitted rather than inventing a theme system.

## Architecture decided
- `src/services/actions/registry.js` — pure data + helpers. Single source of truth. Each
  action: `{ id, label, keywords, group, shortcut?, run(ctx) }`. `shortcut` is data:
  `{ mod?:true, alt?:true, shift?:true, code:'KeyK' }`. Exposes `getActions()`,
  `actionById(id)`, `formatShortcut(shortcut, isMac)`, `matchShortcut(event, shortcut, isMac)`,
  `eventCombo(event, isMac)`, and platform helper `isMac()`. Fase B (CLI) reuses
  `getActions()` / `actionById()` / `run(ctx)` directly.
- `src/services/actions/CommandProvider.jsx` — one global `keydown` listener. Normalizes the
  event (Mod/Alt/Shift + `event.code`), finds the matching action, runs it. Respects
  inputs/textareas/contenteditable (skips bare nav combos while typing; Mod combos still fire
  globally). Owns palette-open and sheet-open state; exposes context
  `{ openPalette, closePalette, openSheet, closeSheet, paletteOpen, sheetOpen, runAction }`.
- `src/services/actions/CommandPalette.jsx` — Mod+K. Fuzzy subsequence matcher (own, no dep),
  combobox/listbox ARIA, `aria-activedescendant`, ↑/↓ + Enter, Esc closes, focus trap + restore.
- `src/services/actions/ShortcutSheet.jsx` — Mod+/ (`Slash`). Dialog overlay listing all
  actions grouped, combos rendered with platform symbols (⌘/⌥/⇧ vs Ctrl/Alt/Shift).
- `src/services/actions/index.js` — barrel.
- CSS appended to `src/styles/components.css` reusing tokens.

## Fuzzy matcher (no dependency)
Subsequence scorer over `label` + `keywords`: returns -1 if not a subsequence, else a score
rewarding consecutive matches, word-boundary starts and earlier matches. Sort desc, drop -1.
Empty query keeps registry order. Simple, dependency-free, good enough for ~10-20 actions.

## Default shortcuts (table)
| Action | id | Combo (Mac) | Combo (Win/Linux) | shortcut data |
|---|---|---|---|---|
| Open command palette | palette.open | ⌘K | Ctrl+K | `{mod, code:'KeyK'}` |
| Open shortcut sheet | sheet.open | ⌘/ | Ctrl+/ | `{mod, code:'Slash'}` |
| Go to dashboard | nav.dashboard | ⌥D | Alt+D | `{alt, code:'KeyD'}` |
| Go to projects | nav.projects | ⌥P | Alt+P | `{alt, code:'KeyP'}` |
| Go to equipment | nav.equipment | ⌥E | Alt+E | `{alt, code:'KeyE'}` |
| Go to team | nav.team | ⌥T | Alt+T | `{alt, code:'KeyT'}` |
| New project | action.newProject | ⌥N | Alt+N | `{alt, code:'KeyN'}` |
| Go to memoria | nav.memoria | ⌥M | Alt+M | `{alt, code:'KeyM'}` |

Letters chosen to minimize collisions: D/P/E/T/N/M map to first letters of destinations and
avoid the Alt+D address-bar clash where possible (documented above; we still bind it because
it is the natural mnemonic for Dashboard and works when the document holds focus).

# CLI Console (Power-user Phase B) — research & design

## Goal
A self-built command-line console (not Vim). Opens with a chord (Mod+Shift+P), plain text
input, no modes. Shell-style history with ArrowUp/ArrowDown inside the input. Reuses the Phase A
action registry, shortcut engine, fuzzy scorer, focus trap and Scrim pattern. No new deps.

## Phase A surface reused (do not duplicate)
- `frontend/src/services/actions/registry.js`: `getActions`, `actionById`, `matchShortcut`,
  `formatShortcut`, `findActionForEvent`, `isMac`, and the single global keydown listener lives
  in `CommandProvider.jsx`. New shortcut `console.open` = `{ mod, shift, code: 'KeyP' }` is added
  there so the existing engine dispatches it.
- `fuzzy.js`: `scoreAction` / `filterActions` reused for the "unknown command → suggestion".
- `CommandContext`/`useCommands` + `ctx` (carries `navigate`, palette/sheet openers). We extend
  `ctx` with `openConsole`/`closeConsole`/`consoleOpen`.
- `useFocusTrap`, `.sun-scrim`/`.sun-scrim--center`, `.kbd` tokens, CSS custom props.
- Cross-platform: chord uses normalized Mod (meta on Mac, ctrl elsewhere) + `event.code` so the
  physical P key matches regardless of layout — identical to Phase A `matchShortcut`.

## Command grammar (self-defined)
Form: `verb [subverb] [positional args] [--flags value]`

Tokenizer: whitespace split with support for quoted segments ("..." / '...'); `--flag value`
and `--flag=value` pulled into a flags map; remaining bare tokens are positional.

Command spec shape:
```
{ name, subverb?, args: [{ name, required, type, choices? }], description, usage, run(ctx, parsed) }
```
`parsed = { args: {<name>: value}, flags: {...}, raw }`.

Validation: required args present; `type: 'enum'` values must be in `choices`; unknown verb →
error + fuzzy suggestion; unknown subverb → error listing valid subverbs.

### Commands
| Command | Args | Reuses | Behaviour |
|---|---|---|---|
| `goto <where>` | where: enum dashboard\|projects\|equipment\|team\|memoria | action registry `run(ctx)` | maps each choice to nav.* action id and runs it |
| `project new` | — | action `action.newProject` | runs its `run(ctx)` |
| `project open <id>` | id (required) | ctx.navigate | `navigate('/app/proyectos')` (list) — there is no per-project detail route, so opens the projects view scoped by id query; falls back gracefully |
| `export memoria <id>` | id (required) | ctx.navigate | `navigate('/app/memoria/<id>')` — the memoria page owns export |
| `help [command]` | command (optional) | command registry | lists commands or prints usage of one |

Notes:
- `goto` choices map: dashboard→nav.dashboard, projects→nav.projects, equipment→nav.equipment,
  team→nav.team, memoria→nav.memoria. Each is an existing action; we call its `run(ctx)`.
- `project open <id>`: router has no `proyectos/:id`; the closest existing target is the design
  wizard `diseno/:id`. We navigate to `/app/diseno/<id>` (opens a project in the editor), which
  is the real "open project" affordance.

## Autocomplete
Tab completes: verb → subverb → enum choices, based on cursor token. While typing, a hint row
shows ranked candidates (fuzzy). Tab with one candidate fills it; with many, fills longest common
prefix.

## History
Array persisted in `localStorage` key `sunalyze.cli.history` (cap 50, dedupe consecutive).
ArrowUp/ArrowDown walk it within the input; a fresh draft is preserved at the bottom of the stack.

## Output / a11y
- `role="dialog"`, `aria-modal`, labelled. `useFocusTrap(true)`, autofocus input, Esc closes and
  restores focus (focus trap cleanup handles restore).
- Output log is a `role="log"` `aria-live="polite"` region; each run appends an entry
  (command echoed + result/error). Errors styled but also announced.

## Files
- new `frontend/src/services/actions/commands.js` — tokenizer, parser, validator, command specs,
  `runCommand`, `autocomplete`.
- new `frontend/src/services/actions/CliConsole.jsx` — dialog UI.
- edit `CommandProvider.jsx` (state + shortcut + ctx), `registry.js` (console.open action),
  `index.js` (exports), `components.css` (`.sun-cli*` styles reusing tokens).
- tests in `frontend/src/test/cli-console.test.jsx`.

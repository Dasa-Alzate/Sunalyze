import { actionById } from './registry'
import { scoreText } from './fuzzy'

export function tokenize(input) {
  const tokens = []
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g
  let m
  while ((m = re.exec(input)) !== null) {
    tokens.push(m[1] ?? m[2] ?? m[3])
  }
  return tokens
}

export function splitTokens(tokens) {
  const positional = []
  const flags = {}
  for (let i = 0; i < tokens.length; i += 1) {
    const tok = tokens[i]
    if (tok.startsWith('--')) {
      const body = tok.slice(2)
      const eq = body.indexOf('=')
      if (eq >= 0) {
        flags[body.slice(0, eq)] = body.slice(eq + 1)
      } else if (i + 1 < tokens.length && !tokens[i + 1].startsWith('--')) {
        flags[body] = tokens[i + 1]
        i += 1
      } else {
        flags[body] = true
      }
    } else {
      positional.push(tok)
    }
  }
  return { positional, flags }
}

const GOTO_TARGETS = {
  dashboard: 'nav.dashboard',
  projects: 'nav.projects',
  equipment: 'nav.equipment',
  team: 'nav.team',
  memoria: 'nav.memoria',
}

const COMMANDS = [
  {
    name: 'goto',
    description: 'Navega a una sección de la app.',
    usage: 'goto <dashboard|projects|equipment|team|memoria>',
    args: [{ name: 'where', required: true, type: 'enum', choices: Object.keys(GOTO_TARGETS) }],
    run: (ctx, parsed) => {
      const action = actionById(GOTO_TARGETS[parsed.args.where])
      action.run(ctx)
      return { ok: true, message: `Navegando a ${parsed.args.where}.` }
    },
  },
  {
    name: 'project',
    subverbs: ['new', 'open'],
    description: 'Crea o abre un proyecto.',
    usage: 'project new | project open <id>',
    variants: {
      new: {
        usage: 'project new',
        args: [],
        run: (ctx) => {
          actionById('action.newProject').run(ctx)
          return { ok: true, message: 'Abriendo el asistente de nuevo proyecto.' }
        },
      },
      open: {
        usage: 'project open <id>',
        args: [{ name: 'id', required: true, type: 'string' }],
        run: (ctx, parsed) => {
          ctx.navigate(`/app/diseno/${encodeURIComponent(parsed.args.id)}`)
          return { ok: true, message: `Abriendo el proyecto ${parsed.args.id}.` }
        },
      },
    },
  },
  {
    name: 'export',
    subverbs: ['memoria'],
    description: 'Exporta documentos.',
    usage: 'export memoria <id>',
    variants: {
      memoria: {
        usage: 'export memoria <id>',
        args: [{ name: 'id', required: true, type: 'string' }],
        run: (ctx, parsed) => {
          ctx.navigate(`/app/memoria/${encodeURIComponent(parsed.args.id)}`)
          return { ok: true, message: `Abriendo la memoria ${parsed.args.id} para exportar.` }
        },
      },
    },
  },
  {
    name: 'help',
    description: 'Lista los comandos o muestra el uso de uno.',
    usage: 'help [comando]',
    args: [{ name: 'command', required: false, type: 'string' }],
    run: (ctx, parsed) => {
      const target = parsed.args.command
      if (!target) {
        const lines = COMMANDS.map((c) => `${c.usage} — ${c.description}`)
        return { ok: true, message: `Comandos:\n${lines.join('\n')}` }
      }
      const cmd = COMMANDS.find((c) => c.name === target)
      if (!cmd) return { ok: false, message: `No existe el comando "${target}".` }
      return { ok: true, message: `${cmd.usage} — ${cmd.description}` }
    },
  },
]

export function getCommands() {
  return COMMANDS
}

export function commandByName(name) {
  return COMMANDS.find((c) => c.name === name)
}

function bestSuggestion(name) {
  let best = null
  let bestScore = 0
  for (const c of COMMANDS) {
    const s = scoreText(name, c.name)
    if (s > bestScore) {
      bestScore = s
      best = c.name
    }
  }
  return best
}

function validateArgs(specs, positional) {
  const args = {}
  for (let i = 0; i < specs.length; i += 1) {
    const spec = specs[i]
    const value = positional[i]
    if (value === undefined) {
      if (spec.required) return { error: `Falta el argumento "${spec.name}".` }
      continue
    }
    if (spec.type === 'enum' && !spec.choices.includes(value)) {
      return { error: `"${value}" no es válido para ${spec.name}. Opciones: ${spec.choices.join(', ')}.` }
    }
    args[spec.name] = value
  }
  return { args }
}

export function parse(input) {
  const tokens = tokenize(input)
  if (tokens.length === 0) return { error: 'Comando vacío.' }
  const [verb, ...rest] = tokens
  const cmd = commandByName(verb)
  if (!cmd) {
    const hint = bestSuggestion(verb)
    return {
      error: `Comando desconocido: "${verb}".${hint ? ` ¿Quisiste decir "${hint}"?` : ''}`,
    }
  }

  if (cmd.variants) {
    const [sub, ...subRest] = rest
    if (!sub) {
      return { error: `"${cmd.name}" requiere un subcomando: ${cmd.subverbs.join(', ')}.` }
    }
    const variant = cmd.variants[sub]
    if (!variant) {
      return { error: `Subcomando desconocido "${sub}". Opciones: ${cmd.subverbs.join(', ')}.` }
    }
    const { positional, flags } = splitTokens(subRest)
    const checked = validateArgs(variant.args, positional)
    if (checked.error) return { error: `${variant.usage} — ${checked.error}` }
    return { command: cmd, run: variant.run, parsed: { args: checked.args, flags, raw: input } }
  }

  const { positional, flags } = splitTokens(rest)
  const checked = validateArgs(cmd.args, positional)
  if (checked.error) return { error: `${cmd.usage} — ${checked.error}` }
  return { command: cmd, run: cmd.run, parsed: { args: checked.args, flags, raw: input } }
}

export function runCommand(input, ctx) {
  const result = parse(input)
  if (result.error) return { ok: false, message: result.error }
  return result.run(ctx, result.parsed)
}

export function autocomplete(input) {
  const endsWithSpace = /\s$/.test(input)
  const tokens = tokenize(input)
  const verb = tokens[0] || ''

  if (tokens.length === 0 || (tokens.length === 1 && !endsWithSpace)) {
    return COMMANDS.map((c) => c.name).filter((n) => n.startsWith(verb))
  }

  const cmd = commandByName(verb)
  if (!cmd) return []

  if (cmd.variants) {
    const subIndex = 1
    const typingSub = tokens.length <= subIndex || (tokens.length === subIndex + 1 && !endsWithSpace)
    if (typingSub) {
      const sub = tokens[subIndex] || ''
      return cmd.subverbs.filter((s) => s.startsWith(sub))
    }
    const variant = cmd.variants[tokens[subIndex]]
    if (!variant) return []
    return enumCandidates(variant.args, tokens.slice(subIndex + 1), endsWithSpace)
  }

  return enumCandidates(cmd.args, tokens.slice(1), endsWithSpace)
}

function enumCandidates(specs, argTokens, endsWithSpace) {
  const idx = endsWithSpace ? argTokens.length : Math.max(0, argTokens.length - 1)
  const spec = specs[idx]
  if (!spec || spec.type !== 'enum') return []
  const current = endsWithSpace ? '' : argTokens[idx] || ''
  return spec.choices.filter((c) => c.startsWith(current))
}

export function commonPrefix(items) {
  if (items.length === 0) return ''
  let prefix = items[0]
  for (const item of items.slice(1)) {
    while (!item.startsWith(prefix)) prefix = prefix.slice(0, -1)
  }
  return prefix
}

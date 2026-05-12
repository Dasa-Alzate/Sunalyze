let macCache = null

export function isMac() {
  if (macCache !== null) return macCache
  if (typeof navigator === 'undefined') {
    macCache = false
    return macCache
  }
  const src = `${navigator.platform || ''} ${navigator.userAgent || ''}`
  macCache = /Mac|iPhone|iPad|iPod/i.test(src)
  return macCache
}

const ACTIONS = [
  {
    id: 'palette.open',
    label: 'Abrir paleta de comandos',
    keywords: ['command', 'palette', 'comandos', 'buscar', 'menu'],
    group: 'General',
    shortcut: { mod: true, code: 'KeyK' },
    run: (ctx) => ctx.openPalette(),
  },
  {
    id: 'sheet.open',
    label: 'Ver atajos de teclado',
    keywords: ['shortcuts', 'atajos', 'teclado', 'ayuda', 'help'],
    group: 'General',
    shortcut: { mod: true, code: 'Slash' },
    run: (ctx) => ctx.openSheet(),
  },
  {
    id: 'nav.dashboard',
    label: 'Ir al resumen',
    keywords: ['dashboard', 'resumen', 'inicio', 'home'],
    group: 'Navegación',
    shortcut: { alt: true, code: 'KeyD' },
    run: (ctx) => ctx.navigate('/app'),
  },
  {
    id: 'nav.projects',
    label: 'Ir a proyectos',
    keywords: ['proyectos', 'projects', 'lista'],
    group: 'Navegación',
    shortcut: { alt: true, code: 'KeyP' },
    run: (ctx) => ctx.navigate('/app/proyectos'),
  },
  {
    id: 'nav.equipment',
    label: 'Ir a equipos',
    keywords: ['equipos', 'equipment', 'librería', 'paneles', 'inversores'],
    group: 'Navegación',
    shortcut: { alt: true, code: 'KeyE' },
    run: (ctx) => ctx.navigate('/app/equipos'),
  },
  {
    id: 'nav.team',
    label: 'Ir al equipo',
    keywords: ['equipo', 'team', 'miembros', 'usuarios'],
    group: 'Navegación',
    shortcut: { alt: true, code: 'KeyT' },
    run: (ctx) => ctx.navigate('/app/equipo'),
  },
  {
    id: 'nav.memoria',
    label: 'Ir a la memoria',
    keywords: ['memoria', 'documento', 'informe', 'report'],
    group: 'Navegación',
    shortcut: { alt: true, code: 'KeyM' },
    run: (ctx) => ctx.navigate('/app/memoria'),
  },
  {
    id: 'action.newProject',
    label: 'Crear proyecto',
    keywords: ['nuevo', 'new', 'crear', 'proyecto', 'project', 'diseño', 'wizard'],
    group: 'Acciones',
    shortcut: { alt: true, code: 'KeyN' },
    run: (ctx) => ctx.navigate('/app/diseno'),
  },
]

export function getActions() {
  return ACTIONS
}

export function actionById(id) {
  return ACTIONS.find((a) => a.id === id)
}

const CODE_LABELS = { Slash: '/', Comma: ',', Period: '.', Backslash: '\\' }

function codeLabel(code) {
  if (code in CODE_LABELS) return CODE_LABELS[code]
  if (code.startsWith('Key')) return code.slice(3)
  if (code.startsWith('Digit')) return code.slice(5)
  return code
}

export function formatShortcut(shortcut, mac = isMac()) {
  if (!shortcut) return ''
  const parts = []
  if (shortcut.mod) parts.push(mac ? '⌘' : 'Ctrl')
  if (shortcut.alt) parts.push(mac ? '⌥' : 'Alt')
  if (shortcut.shift) parts.push(mac ? '⇧' : 'Shift')
  parts.push(codeLabel(shortcut.code))
  return parts.join(mac ? '' : '+')
}

export function matchShortcut(event, shortcut, mac = isMac()) {
  if (!shortcut || event.code !== shortcut.code) return false
  const mod = mac ? event.metaKey : event.ctrlKey
  const otherMod = mac ? event.ctrlKey : event.metaKey
  if (Boolean(shortcut.mod) !== mod) return false
  if (Boolean(shortcut.alt) !== event.altKey) return false
  if (shortcut.shift !== undefined && Boolean(shortcut.shift) !== event.shiftKey) return false
  if (otherMod) return false
  return true
}

export function findActionForEvent(event, mac = isMac()) {
  return ACTIONS.find((a) => matchShortcut(event, a.shortcut, mac))
}

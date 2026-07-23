const BY_CODE_PREFIX = [
  ['catalog.', { href: '/app/equipos?tab=marketplace', view: 'equipos' }],
  ['equipment.', { href: '/app/equipos', view: 'equipos' }],
  ['panel.', { href: '/app/equipos', view: 'equipos' }],
  ['inverter.', { href: '/app/equipos', view: 'equipos' }],
  ['battery.', { href: '/app/equipos', view: 'equipos' }],
  ['wire.', { href: '/app/equipos', view: 'equipos' }],
  ['project.', { href: '/app/proyectos', view: 'proyectos' }],
  ['memoria.', { href: '/app/memoria', view: 'memoria' }],
  ['document.', { href: '/app/memoria', view: 'memoria' }],
  ['template.', { href: '/app/plantillas', view: 'plantillas' }],
  ['flag.', { href: '/app/configuracion', view: 'configuracion' }],
  ['org.', { href: '/app/configuracion', view: 'configuracion' }],
]

const BY_PATH_PREFIX = [
  ['/api/panels', { href: '/app/equipos', view: 'equipos' }],
  ['/api/inverters', { href: '/app/equipos', view: 'equipos' }],
  ['/api/batteries', { href: '/app/equipos', view: 'equipos' }],
  ['/api/wires', { href: '/app/equipos', view: 'equipos' }],
  ['/api/catalogs', { href: '/app/equipos?tab=marketplace', view: 'equipos' }],
  ['/api/marketplace', { href: '/app/equipos?tab=marketplace', view: 'equipos' }],
  ['/api/projects', { href: '/app/proyectos', view: 'proyectos' }],
  ['/api/templates', { href: '/app/plantillas', view: 'plantillas' }],
  ['/api/panel-analysis', { href: '/app/equipos', view: 'equipos' }],
]

export function solutionFor(error) {
  if (!error) return null
  const code = error.code || ''
  if (code.startsWith('auth.') || code === 'error.internal') return null
  const byCode = BY_CODE_PREFIX.find(([prefix]) => code.startsWith(prefix))
  if (byCode) return byCode[1]
  const path = error.path || ''
  const byPath = BY_PATH_PREFIX.find(([prefix]) => path.startsWith(prefix))
  return byPath ? byPath[1] : null
}

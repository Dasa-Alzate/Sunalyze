const ROUTES = [
  { match: /^\/app\/?$/, view: 'resumen' },
  { match: /^\/app\/proyectos/, view: 'proyectos' },
  { match: /^\/app\/diseno/, view: 'diseno' },
  { match: /^\/app\/equipos/, view: 'equipos' },
  { match: /^\/app\/equipo\b/, view: 'equipo' },
  { match: /^\/app\/memoria/, view: 'memoria' },
  { match: /^\/app\/legalizacion/, view: 'legalizacion' },
  { match: /^\/app\/modulos/, view: 'modulos' },
  { match: /^\/app\/plantillas/, view: 'plantillas' },
  { match: /^\/app\/finanzas/, view: 'finanzas' },
  { match: /^\/app\/posventa/, view: 'posventa' },
  { match: /^\/app\/actividad/, view: 'actividad' },
  { match: /^\/app\/papelera/, view: 'papelera' },
  { match: /^\/app\/configuracion/, view: 'configuracion' },
]

export function resolveView(pathname) {
  const hit = ROUTES.find((r) => r.match.test(pathname))
  return hit ? hit.view : 'app'
}

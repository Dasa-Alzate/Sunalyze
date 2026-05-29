export const INSTALLATION_STATUS = {
  operativa: { label: 'Operativa', tone: 'success', icon: 'circle-check' },
  incidencia: { label: 'Incidencia', tone: 'danger', icon: 'alert-triangle' },
  mantenimiento: { label: 'Mantenimiento', tone: 'warning', icon: 'wrench' },
  baja: { label: 'Baja', tone: 'neutral', icon: 'circle-off' },
}

export const INSTALLATION_STATUS_OPTIONS = Object.keys(INSTALLATION_STATUS).map((value) => ({
  value,
  label: INSTALLATION_STATUS[value].label,
}))

export const VISIT_KIND = {
  preventivo: { label: 'Preventivo', tone: 'info' },
  correctivo: { label: 'Correctivo', tone: 'warning' },
}

export const VISIT_STATUS = {
  programada: { label: 'Programada', tone: 'info', icon: 'calendar-clock' },
  realizada: { label: 'Realizada', tone: 'success', icon: 'check' },
  cancelada: { label: 'Cancelada', tone: 'neutral', icon: 'x' },
}

export const INCIDENT_SEVERITY = {
  baja: { label: 'Baja', tone: 'neutral' },
  media: { label: 'Media', tone: 'info' },
  alta: { label: 'Alta', tone: 'warning' },
  critica: { label: 'Crítica', tone: 'danger' },
}

export const INCIDENT_STATUS = {
  abierta: { label: 'Abierta', tone: 'danger', icon: 'circle-dot' },
  en_proceso: { label: 'En proceso', tone: 'warning', icon: 'loader' },
  resuelta: { label: 'Resuelta', tone: 'success', icon: 'circle-check' },
}

export function meta(map, key) {
  return map[key] || { label: key || '—', tone: 'neutral' }
}

export function today() {
  return new Date().toISOString().slice(0, 10)
}

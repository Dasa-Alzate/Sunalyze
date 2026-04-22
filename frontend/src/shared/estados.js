export const ESTADOS = {
  memoria: { label: 'Memoria', tone: 'success', dot: 'valid' },
  diseno: { label: 'Diseño', tone: 'warning', dot: 'warn' },
  borrador: { label: 'Borrador', tone: 'neutral', dot: 'pending' },
}

export function estadoMeta(estado) {
  return ESTADOS[estado] || ESTADOS.borrador
}

export function relativo(iso) {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return '—'
  const diff = Date.now() - then
  const min = Math.round(diff / 60000)
  if (min < 1) return 'ahora'
  if (min < 60) return `hace ${min} min`
  const h = Math.round(min / 60)
  if (h < 24) return `hace ${h} h`
  const d = Math.round(h / 24)
  if (d < 7) return `hace ${d} día${d > 1 ? 's' : ''}`
  const sem = Math.round(d / 7)
  if (sem < 5) return `hace ${sem} sem`
  const mes = Math.round(d / 30)
  return `hace ${mes} mes${mes > 1 ? 'es' : ''}`
}

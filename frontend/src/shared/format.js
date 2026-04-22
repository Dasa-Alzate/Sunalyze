export function num(value, decimals = 2) {
  if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('es-ES', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function int(value) {
  if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '—'
  return Math.round(Number(value)).toLocaleString('es-ES')
}

export function dec(value) {
  if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('es-ES', { maximumFractionDigits: 2 })
}

export function pct(value, decimals = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return num(Number(value) * 100, decimals)
}

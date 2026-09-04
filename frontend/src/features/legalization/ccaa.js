export const CCAA_OPTIONS = [
  { value: '', label: 'Sin asignar' },
  { value: 'andalucia', label: 'Andalucía' },
  { value: 'aragon', label: 'Aragón' },
  { value: 'asturias', label: 'Principado de Asturias' },
  { value: 'illes balears', label: 'Illes Balears' },
  { value: 'canarias', label: 'Canarias' },
  { value: 'cantabria', label: 'Cantabria' },
  { value: 'castilla-la mancha', label: 'Castilla-La Mancha' },
  { value: 'castilla y leon', label: 'Castilla y León' },
  { value: 'cataluna', label: 'Cataluña' },
  { value: 'comunitat valenciana', label: 'Comunitat Valenciana' },
  { value: 'extremadura', label: 'Extremadura' },
  { value: 'galicia', label: 'Galicia' },
  { value: 'la rioja', label: 'La Rioja' },
  { value: 'madrid', label: 'Comunidad de Madrid' },
  { value: 'murcia', label: 'Región de Murcia' },
  { value: 'navarra', label: 'Comunidad Foral de Navarra' },
  { value: 'pais vasco', label: 'País Vasco' },
]

const ALIASES = {
  'comunidad valenciana': 'comunitat valenciana',
  'region de murcia': 'murcia',
  catalunya: 'cataluna',
  euskadi: 'pais vasco',
  'comunidad de madrid': 'madrid',
  'comunidad foral de navarra': 'navarra',
  nafarroa: 'navarra',
  'principado de asturias': 'asturias',
  asturies: 'asturias',
  'islas baleares': 'illes balears',
}

function norm(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

export function ccaaLabel(value) {
  return CCAA_OPTIONS.find((o) => o.value === value)?.label || value
}

export function ccaaFromNominatimState(state) {
  const n = norm(state)
  if (!n) return null
  const key = ALIASES[n] || n
  return CCAA_OPTIONS.some((o) => o.value === key) ? key : null
}

export async function detectCcaa(lat, lon) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=8&addressdetails=1&lat=${lat}&lon=${lon}`,
      { headers: { 'Accept-Language': 'es' } },
    )
    const data = await res.json()
    return ccaaFromNominatimState(data?.address?.state)
  } catch {
    return null
  }
}

export const DOCUMENT_KINDS = [
  { value: 'memoria_calculo', label: 'Memoria de cálculo' },
  { value: 'documento_legal', label: 'Documento legal' },
  { value: 'propuesta_comercial', label: 'Propuesta comercial' },
  { value: 'analisis_caso', label: 'Análisis de caso' },
]

export function kindLabel(kind, kinds) {
  const list = kinds && kinds.length ? kinds : DOCUMENT_KINDS
  return list.find((k) => k.value === kind)?.label || kind
}

export const TEMPLATE_STAGES = [
  { value: 'diseno', label: 'Diseño' },
  { value: 'legalizacion', label: 'Legalización' },
  { value: 'entrega', label: 'Entrega' },
  { value: 'posventa', label: 'Posventa' },
]

export function stageLabel(stage) {
  return TEMPLATE_STAGES.find((s) => s.value === stage)?.label || stage
}

export const FILTERS = [
  { value: '', label: 'Sin formato', args: [] },
  { value: 'number', label: 'Número (decimales)', args: [{ key: 'decimals', label: 'Decimales', default: 2 }] },
  { value: 'thousands', label: 'Miles + decimales', args: [{ key: 'decimals', label: 'Decimales', default: 2 }] },
  { value: 'ellipsis', label: 'Recortar texto (…)', args: [{ key: 'max', label: 'Máx. caracteres', default: 40 }] },
  { value: 'upper', label: 'MAYÚSCULAS', args: [] },
  { value: 'lower', label: 'minúsculas', args: [] },
]

export function buildExpression(path, filterValue, argValues) {
  if (!filterValue) return `{{ ${path} }}`
  const filterDef = FILTERS.find((f) => f.value === filterValue)
  const args = (filterDef?.args || [])
    .map((a) => argValues[a.key])
    .filter((v) => v !== undefined && v !== '')
  const call = args.length ? `${filterValue}(${args.join(', ')})` : filterValue
  return `{{ ${path} | ${call} }}`
}

export const STATUS_TONES = {
  draft: { tone: 'neutral', label: 'Borrador' },
  published: { tone: 'success', label: 'Publicada' },
  archived: { tone: 'warning', label: 'Archivada' },
}

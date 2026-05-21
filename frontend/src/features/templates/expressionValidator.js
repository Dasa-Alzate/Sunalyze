const MAX_EXPRESSION_LENGTH = 500

const FILTER_ARITY = {
  number: { min: 0, max: 1 },
  thousands: { min: 0, max: 1 },
  ellipsis: { min: 1, max: 1 },
  upper: { min: 0, max: 0 },
  lower: { min: 0, max: 0 },
}

const NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$/

function rejectUnsafeName(name) {
  for (const part of name.split('.')) {
    if (!part) return `Nombre inválido en la expresión: '${name}'.`
    if (part.startsWith('_') || part.includes('__')) {
      return `Acceso prohibido a atributo interno: '${name}'.`
    }
  }
  return null
}

function validateFilterCall(segment) {
  const trimmed = segment.trim()
  if (!trimmed) return 'Se esperaba el nombre de un filtro tras "|".'
  const call = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(([^)]*)\))?$/)
  if (!call) return `Filtro mal formado: '${trimmed}'.`
  const name = call[1]
  const arity = FILTER_ARITY[name]
  if (!arity) return `Filtro desconocido: '${name}'.`
  const rawArgs = call[2]
  let argCount = 0
  if (rawArgs !== undefined && rawArgs.trim() !== '') {
    argCount = rawArgs.split(',').map((a) => a.trim()).length
    if (rawArgs.split(',').some((a) => a.trim() === '')) {
      return `Argumentos de filtro mal formados en '${name}'.`
    }
  }
  if (argCount < arity.min || argCount > arity.max) {
    return `El filtro '${name}' no admite ${argCount} argumento(s).`
  }
  return null
}

function validateExpression(inner) {
  const source = inner.trim()
  if (!source) return 'Expresión vacía.'
  if (source.length > MAX_EXPRESSION_LENGTH) return 'Expresión demasiado larga.'
  const segments = source.split('|')
  const base = segments[0].trim()
  if (!base) return 'Falta la expresión antes del primer filtro.'
  const isSimpleName = NAME_RE.test(base)
  const isLiteral = /^-?\d+(?:\.\d+)?$/.test(base) || /^'[^']*'$/.test(base) || /^"[^"]*"$/.test(base)
  if (isSimpleName) {
    const unsafe = rejectUnsafeName(base)
    if (unsafe) return unsafe
  } else if (!isLiteral) {
    for (const m of base.matchAll(/[A-Za-z_][A-Za-z0-9_.]*/g)) {
      const unsafe = rejectUnsafeName(m[0])
      if (unsafe) return unsafe
    }
  }
  for (const seg of segments.slice(1)) {
    const err = validateFilterCall(seg)
    if (err) return err
  }
  return null
}

export function validateBody(text) {
  const errors = []
  if (!text) return errors
  const open = (text.match(/\{\{/g) || []).length
  const close = (text.match(/\}\}/g) || []).length
  if (open !== close) {
    errors.push({ expr: '', start: 0, end: 0, message: 'Delimitadores {{ }} sin balancear.' })
    return errors
  }
  const re = /\{\{([\s\S]*?)\}\}/g
  let match
  while ((match = re.exec(text)) !== null) {
    const message = validateExpression(match[1])
    if (message) {
      errors.push({
        expr: match[1].trim(),
        start: match.index,
        end: match.index + match[0].length,
        message,
      })
    }
  }
  return errors
}

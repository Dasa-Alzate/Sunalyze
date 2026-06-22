import { uiLocaleTag, TECHNICAL_LOCALE } from '@/services/i18n/locale'

const PLACEHOLDER = '—'

function isBlank(value) {
  return value === null || value === undefined || value === '' || Number.isNaN(Number(value))
}

export function num(value, decimals = 2) {
  if (isBlank(value)) return PLACEHOLDER
  return Number(value).toLocaleString(uiLocaleTag(), {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function int(value) {
  if (isBlank(value)) return PLACEHOLDER
  return Math.round(Number(value)).toLocaleString(uiLocaleTag())
}

export function dec(value) {
  if (isBlank(value)) return PLACEHOLDER
  return Number(value).toLocaleString(uiLocaleTag(), { maximumFractionDigits: 2 })
}

export function pct(value, decimals = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return PLACEHOLDER
  return num(Number(value) * 100, decimals)
}

export function date(value, options = { dateStyle: 'medium' }) {
  if (!value) return PLACEHOLDER
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return PLACEHOLDER
  return d.toLocaleDateString(uiLocaleTag(), options)
}

export function techNum(value, decimals = 2) {
  if (isBlank(value)) return PLACEHOLDER
  return Number(value).toLocaleString(TECHNICAL_LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function techDec(value) {
  if (isBlank(value)) return PLACEHOLDER
  return Number(value).toLocaleString(TECHNICAL_LOCALE, { maximumFractionDigits: 2 })
}

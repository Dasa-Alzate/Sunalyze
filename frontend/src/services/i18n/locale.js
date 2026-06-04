import { DEFAULT_LOCALE } from './config'

export const TECHNICAL_LOCALE = 'es-ES'

const LOCALE_TAGS = { es: 'es-ES', en: 'en-GB' }

let activeLocale = DEFAULT_LOCALE

export function setActiveLocale(locale) {
  activeLocale = locale || DEFAULT_LOCALE
}

export function getActiveLocale() {
  return activeLocale
}

export function uiLocaleTag() {
  return LOCALE_TAGS[activeLocale] || LOCALE_TAGS[DEFAULT_LOCALE]
}

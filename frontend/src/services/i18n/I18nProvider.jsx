import { useEffect } from 'react'
import { I18nextProvider } from 'react-i18next'
import i18n, { normalizeLocale, DEFAULT_LOCALE } from './config'
import { setActiveLocale } from './locale'

export function applyLocale(locale) {
  const lang = normalizeLocale(locale) || DEFAULT_LOCALE
  setActiveLocale(lang)
  if (i18n.language !== lang) i18n.changeLanguage(lang)
  if (typeof document !== 'undefined') document.documentElement.lang = lang
  return lang
}

export function I18nProvider({ children }) {
  useEffect(() => {
    const sync = (lng) => setActiveLocale(normalizeLocale(lng) || DEFAULT_LOCALE)
    sync(i18n.language)
    i18n.on('languageChanged', sync)
    return () => i18n.off('languageChanged', sync)
  }, [])
  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
}

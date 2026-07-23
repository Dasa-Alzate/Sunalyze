import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import esNav from '@/locales/es/nav.json'
import esCommon from '@/locales/es/common.json'
import esAuth from '@/locales/es/auth.json'
import esSettings from '@/locales/es/settings.json'
import esErrors from '@/locales/es/errors.json'
import esNotifications from '@/locales/es/notifications.json'
import esActivity from '@/locales/es/activity.json'
import esTrash from '@/locales/es/trash.json'
import esTemplates from '@/locales/es/templates.json'
import esBranding from '@/locales/es/branding.json'
import esCircuit from '@/locales/es/circuit.json'
import esAssist from '@/locales/es/assist.json'

import enNav from '@/locales/en/nav.json'
import enCommon from '@/locales/en/common.json'
import enAuth from '@/locales/en/auth.json'
import enSettings from '@/locales/en/settings.json'
import enErrors from '@/locales/en/errors.json'
import enNotifications from '@/locales/en/notifications.json'
import enActivity from '@/locales/en/activity.json'
import enTrash from '@/locales/en/trash.json'
import enTemplates from '@/locales/en/templates.json'
import enBranding from '@/locales/en/branding.json'
import enCircuit from '@/locales/en/circuit.json'
import enAssist from '@/locales/en/assist.json'

export const SUPPORTED_LOCALES = ['es', 'en']
export const DEFAULT_LOCALE = 'es'

const resources = {
  es: { nav: esNav, common: esCommon, auth: esAuth, settings: esSettings, errors: esErrors, notifications: esNotifications, activity: esActivity, trash: esTrash, templates: esTemplates, branding: esBranding, circuit: esCircuit, assist: esAssist },
  en: { nav: enNav, common: enCommon, auth: enAuth, settings: enSettings, errors: enErrors, notifications: enNotifications, activity: enActivity, trash: enTrash, templates: enTemplates, branding: enBranding, circuit: enCircuit, assist: enAssist },
}

export function normalizeLocale(value) {
  if (!value) return null
  const lang = String(value).trim().toLowerCase().replace('_', '-').split('-')[0]
  return SUPPORTED_LOCALES.includes(lang) ? lang : null
}

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources,
    lng: DEFAULT_LOCALE,
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: SUPPORTED_LOCALES,
    ns: ['nav', 'common', 'auth', 'settings', 'errors', 'notifications', 'activity', 'trash', 'templates', 'branding', 'circuit', 'assist'],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  })
}

export default i18n

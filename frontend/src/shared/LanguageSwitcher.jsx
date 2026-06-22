import { useId } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/services/auth'
import { toast } from '@/services/toast'
import { messageForError } from '@/services/i18n'
import { SUPPORTED_LOCALES } from '@/services/i18n'

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation('settings')
  const { setLocale, isAuthenticated } = useAuth()
  const selectId = useId()

  async function onChange(e) {
    const next = e.target.value
    const prev = i18n.language
    i18n.changeLanguage(next)
    if (!isAuthenticated) return
    try {
      await setLocale(next)
      toast('success', t('language.changed'))
    } catch (err) {
      i18n.changeLanguage(prev)
      toast('error', t('language.error'), messageForError(err, t))
    }
  }

  return (
    <div className="sun-langswitch">
      <label className="sr-only" htmlFor={selectId}>{t('language.label')}</label>
      <select
        id={selectId}
        className="sun-select sun-select--sm"
        value={i18n.language}
        onChange={onChange}
      >
        {SUPPORTED_LOCALES.map((code) => (
          <option key={code} value={code}>{t(`language.${code}`)}</option>
        ))}
      </select>
    </div>
  )
}

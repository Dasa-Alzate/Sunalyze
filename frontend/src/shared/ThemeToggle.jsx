import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { IconBtn } from '@/shared/ui'
import { currentTheme, toggleTheme } from '@/services/theme'

export function ThemeToggle() {
  const { t } = useTranslation('settings')
  const [theme, setThemeState] = useState(currentTheme)
  const dark = theme === 'dark'
  return (
    <IconBtn
      icon={dark ? 'sun' : 'moon'}
      label={t(dark ? 'theme.toLight' : 'theme.toDark')}
      size="sm"
      onClick={() => setThemeState(toggleTheme())}
    />
  )
}

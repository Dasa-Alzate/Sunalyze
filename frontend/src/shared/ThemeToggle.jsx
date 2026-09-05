import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { IconBtn } from '@/shared/ui'
import { currentTheme, toggleTheme, subscribeTheme } from '@/services/theme'

export function ThemeToggle(props) {
  const { t } = useTranslation('settings')
  const [theme, setThemeState] = useState(currentTheme)
  useEffect(() => subscribeTheme(setThemeState), [])
  const dark = theme === 'dark'
  return (
    <IconBtn
      icon={dark ? 'sun' : 'moon'}
      label={t(dark ? 'theme.toLight' : 'theme.toDark')}
      size="sm"
      onClick={() => setThemeState(toggleTheme())}
      {...props}
    />
  )
}

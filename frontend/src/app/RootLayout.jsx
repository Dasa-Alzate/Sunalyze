import { Outlet } from 'react-router-dom'
import { TransitionProvider } from '@/services/transition'
import { ToastHost } from '@/services/toast'
import { AuthProvider } from '@/services/auth'
import { CommandProvider } from '@/services/actions'
import { I18nProvider } from '@/services/i18n'

export function RootLayout() {
  return (
    <I18nProvider>
      <AuthProvider>
        <TransitionProvider>
          <CommandProvider>
            <Outlet />
            <ToastHost />
          </CommandProvider>
        </TransitionProvider>
      </AuthProvider>
    </I18nProvider>
  )
}

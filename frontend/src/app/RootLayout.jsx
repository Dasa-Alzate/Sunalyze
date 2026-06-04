import { Outlet } from 'react-router-dom'
import { TransitionProvider } from '@/services/transition'
import { ToastHost } from '@/services/toast'
import { AuthProvider } from '@/services/auth'
import { CommandProvider } from '@/services/actions'
import { I18nProvider } from '@/services/i18n'
import { NotificationsProvider } from '@/services/notifications'

export function RootLayout() {
  return (
    <I18nProvider>
      <AuthProvider>
        <TransitionProvider>
          <NotificationsProvider>
            <CommandProvider>
              <Outlet />
              <ToastHost />
            </CommandProvider>
          </NotificationsProvider>
        </TransitionProvider>
      </AuthProvider>
    </I18nProvider>
  )
}

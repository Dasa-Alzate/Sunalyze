import { Outlet } from 'react-router-dom'
import { TransitionProvider } from '@/services/transition'
import { ToastHost } from '@/services/toast'
import { AuthProvider } from '@/services/auth'
import { CommandProvider } from '@/services/actions'

export function RootLayout() {
  return (
    <AuthProvider>
      <TransitionProvider>
        <CommandProvider>
          <Outlet />
          <ToastHost />
        </CommandProvider>
      </TransitionProvider>
    </AuthProvider>
  )
}

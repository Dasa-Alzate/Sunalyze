import { Outlet } from 'react-router-dom'
import { TransitionProvider } from '@/services/transition'
import { ToastHost } from '@/services/toast'
import { AuthProvider } from '@/services/auth'

export function RootLayout() {
  return (
    <AuthProvider>
      <TransitionProvider>
        <Outlet />
        <ToastHost />
      </TransitionProvider>
    </AuthProvider>
  )
}

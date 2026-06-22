import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthProvider'
import { Spinner } from '@/shared/ui'

export function RequireFlag({ flag: flagKey, children }) {
  const { loading, isAuthenticated, flag } = useAuth()
  if (loading) {
    return <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}><Spinner label="Comprobando acceso…" /></div>
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!flag(flagKey)) return <Navigate to="/app" replace />
  return children
}

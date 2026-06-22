import { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
import { api, setUnauthorizedHandler } from '@/api/client'
import { applyLocale } from '@/services/i18n'

const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(undefined)

  const applySession = useCallback((data) => {
    applyLocale(data?.user?.locale || data?.locale)
    setSession({
      user: data?.user || null,
      role: data?.role || null,
      permissions: data?.permissions || [],
      flags: data?.flags || {},
      locale: data?.user?.locale || data?.locale || null,
    })
  }, [])

  useEffect(() => {
    let alive = true
    api.auth.me()
      .then((d) => alive && applySession(d))
      .catch(() => alive && applySession(null))
    return () => { alive = false }
  }, [applySession])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      applySession(null)
      if (typeof window !== 'undefined' && window.location.pathname.startsWith('/app')) {
        window.location.assign('/login')
      }
    })
    return () => setUnauthorizedHandler(null)
  }, [applySession])

  const login = useCallback(async (credentials) => {
    const d = await api.auth.login(credentials)
    applySession(d)
    return d.user
  }, [applySession])

  const register = useCallback(async (data) => {
    const d = await api.auth.register(data)
    applySession(d)
    return d
  }, [applySession])

  const logout = useCallback(async () => {
    try { await api.auth.logout() } finally { applySession(null) }
  }, [applySession])

  const refresh = useCallback(async () => {
    const d = await api.auth.me()
    applySession(d)
    return d.user
  }, [applySession])

  const setLocale = useCallback(async (locale) => {
    const d = await api.auth.updateLocale(locale)
    applySession(d)
    return d.user
  }, [applySession])

  const user = session?.user || null
  const permissions = session?.permissions || []

  const can = useCallback((perm) => permissions.includes(perm), [permissions])

  const flags = session?.flags || {}
  const flag = useCallback((key) => !!flags[key], [flags])

  const value = useMemo(() => ({
    user,
    role: session?.role || null,
    permissions,
    flags,
    loading: session === undefined,
    isAuthenticated: !!user,
    isPlatformAdmin: !!user?.is_superadmin,
    org: user?.organizations?.[0] || null,
    locale: session?.locale || null,
    can,
    flag,
    login,
    register,
    logout,
    refresh,
    setLocale,
  }), [user, session, permissions, flags, can, flag, login, register, logout, refresh, setLocale])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

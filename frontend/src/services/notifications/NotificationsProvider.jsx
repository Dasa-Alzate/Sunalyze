import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '@/api/client'
import { useAuth } from '@/services/auth'
import { NotificationsContext } from './context'

const POLL_MS = 45000
const PER_PAGE = 20

export function NotificationsProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [count, setCount] = useState(0)
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(false)
  const aliveRef = useRef(true)

  useEffect(() => {
    aliveRef.current = true
    return () => { aliveRef.current = false }
  }, [])

  const refreshCount = useCallback(async () => {
    try {
      const d = await api.notifications.unreadCount()
      if (aliveRef.current) setCount(d?.unread_count || 0)
    } catch {
      // contador best-effort: un fallo de red no rompe la UI
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      setCount(0)
      return undefined
    }
    refreshCount()
    let timer = null
    const tick = () => {
      if (!document.hidden) refreshCount()
    }
    const onVisibility = () => {
      if (!document.hidden) refreshCount()
    }
    timer = setInterval(tick, POLL_MS)
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      if (timer) clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [isAuthenticated, refreshCount])

  const loadPage = useCallback(async (target) => {
    setLoading(true)
    setError(null)
    try {
      const d = await api.notifications.list(target, PER_PAGE)
      if (!aliveRef.current) return
      setItems((prev) => (target === 1 ? d.items : [...prev, ...d.items]))
      setPage(d.page)
      setTotal(d.total)
      setCount(d.unread_count || 0)
    } catch (e) {
      if (aliveRef.current) setError(e.message)
    } finally {
      if (aliveRef.current) setLoading(false)
    }
  }, [])

  const loadFirst = useCallback(() => loadPage(1), [loadPage])
  const loadMore = useCallback(() => loadPage(page + 1), [loadPage, page])

  const markRead = useCallback(async (id) => {
    const target = items.find((n) => n.id === id)
    if (target && target.read_at) return
    const updated = await api.notifications.markRead(id)
    if (!aliveRef.current) return
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, ...updated } : n)))
    refreshCount()
  }, [items, refreshCount])

  const readAll = useCallback(async () => {
    await api.notifications.readAll()
    if (!aliveRef.current) return
    const now = new Date().toISOString()
    setItems((prev) => prev.map((n) => (n.read_at ? n : { ...n, read_at: now, is_read: true })))
    setCount(0)
  }, [])

  const hasMore = items.length < total

  const value = useMemo(() => ({
    count,
    items,
    page,
    hasMore,
    loading,
    error,
    open,
    setOpen,
    loadFirst,
    loadMore,
    markRead,
    readAll,
  }), [count, items, page, hasMore, loading, error, open, loadFirst, loadMore, markRead, readAll])

  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>
}

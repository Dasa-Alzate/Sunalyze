import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter } from 'react-router-dom'

const notifItems = [
  { id: 1, type: 'project.shared', link: '/proyectos/10', read_at: null, is_read: false, created_at: '2026-06-20T10:00:00' },
  { id: 2, type: 'membership.added', link: '/equipo', read_at: '2026-06-19T10:00:00', is_read: true, created_at: '2026-06-19T10:00:00' },
]

const pendingWork = {
  items: [
    { type: 'projects.draft', label: 'Proyectos en borrador', count: 3, link: '/proyectos?estado=borrador' },
    { type: 'invitations.pending', label: 'Invitaciones pendientes', count: 1, link: '/equipo' },
  ],
  total: 4,
}

const api = {
  notifications: {
    list: vi.fn(() => Promise.resolve({ items: notifItems, page: 1, per_page: 20, total: 2, unread_count: 1 })),
    unreadCount: vi.fn(() => Promise.resolve({ unread_count: 1 })),
    markRead: vi.fn((id) => Promise.resolve({ id, read_at: '2026-06-21T10:00:00', is_read: true })),
    readAll: vi.fn(() => Promise.resolve({ ok: true, updated: 1 })),
  },
  pendingWork: {
    get: vi.fn(() => Promise.resolve(pendingWork)),
  },
}

vi.mock('@/api/client', () => ({ api, ApiError: class ApiError extends Error {} }))

const navigate = vi.fn()
vi.mock('@/services/transition', () => ({
  useTransition: () => ({ navigate, phase: 'idle', busy: false }),
}))

vi.mock('@/services/auth', () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))

let NotificationsProvider, NotificationBell, NotificationCenter, PendingWorkPanel

beforeEach(async () => {
  vi.clearAllMocks()
  ;({ NotificationsProvider } = await import('@/services/notifications'))
  ;({ default: NotificationBell } = await import('@/features/notifications/NotificationBell'))
  ;({ default: NotificationCenter } = await import('@/features/notifications/NotificationCenter'))
  ;({ default: PendingWorkPanel } = await import('@/features/notifications/PendingWorkPanel'))
})

function withProviders(ui) {
  return (
    <MemoryRouter>
      <NotificationsProvider>{ui}</NotificationsProvider>
    </MemoryRouter>
  )
}

describe('notifications a11y', () => {
  it('bell has no axe violations and an accessible name with count', async () => {
    const { container } = render(withProviders(<NotificationBell />))
    await waitFor(() => expect(api.notifications.unreadCount).toHaveBeenCalled())
    const bell = await screen.findByRole('button', { name: /sin leer|unread/i })
    expect(bell).toBeInTheDocument()
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('notification center has no axe violations', async () => {
    const { container } = render(withProviders(<NotificationCenter onClose={() => {}} />))
    await waitFor(() => expect(api.notifications.list).toHaveBeenCalled())
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('pending work panel has no axe violations', async () => {
    const { container } = render(withProviders(<PendingWorkPanel />))
    await waitFor(() => expect(api.pendingWork.get).toHaveBeenCalled())
    expect(await screen.findByText('3')).toBeInTheDocument()
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })
})

describe('badge reflects unread-count and decrements on mark-read', () => {
  it('shows the mocked unread count and decrements after marking one read', async () => {
    render(withProviders(<NotificationBell />))

    await waitFor(() => expect(api.notifications.unreadCount).toHaveBeenCalled())
    const bell = await screen.findByRole('button', { name: /1 sin leer|1 unread/i })
    expect(bell).toHaveTextContent('1')

    fireEvent.click(bell)
    await waitFor(() => expect(api.notifications.list).toHaveBeenCalled())

    api.notifications.unreadCount.mockResolvedValue({ unread_count: 0 })
    const markBtns = await screen.findAllByRole('button', { name: /marcar como leída|mark as read/i })
    fireEvent.click(markBtns[0])

    await waitFor(() => expect(api.notifications.markRead).toHaveBeenCalledWith(1))

    fireEvent.keyDown(document, { key: 'Escape' })
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /1 sin leer|1 unread/i })).not.toBeInTheDocument()
    })
    expect(await screen.findByRole('button', { name: /^notificaciones$|^notifications$/i })).toBeInTheDocument()
  })
})

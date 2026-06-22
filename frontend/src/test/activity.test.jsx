import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter } from 'react-router-dom'

const auditItems = [
  { id: 3, action: 'project.create', actor_email: 'ana@example.com', entity_type: 'project', entity_id: 7, link: '/app/proyectos/7', created_at: '2026-06-20T10:00:00' },
  { id: 2, action: 'catalog.restore', actor_email: 'ana@example.com', entity_type: 'catalog', entity_id: 1, link: '/app/equipos', created_at: '2026-06-19T09:00:00' },
  { id: 1, action: 'auth.login', actor_email: null, entity_type: null, entity_id: null, link: null, created_at: '2026-06-18T08:00:00' },
]

const deletedProjects = [
  { id: 11, cliente: 'Cliente Borrado', deleted_at: '2026-06-15T12:00:00' },
]
const deletedCatalogs = [
  { id: 21, nombre: 'Catálogo Borrado', own: true, deleted_at: '2026-06-14T12:00:00' },
]

const api = {
  audit: {
    feed: vi.fn(() => Promise.resolve({ items: auditItems, total: 3, limit: 25, offset: 0, has_more: false })),
  },
  projects: {
    listDeleted: vi.fn(() => Promise.resolve(deletedProjects)),
    restore: vi.fn((id) => Promise.resolve({ id })),
  },
  catalogs: {
    listDeleted: vi.fn(() => Promise.resolve(deletedCatalogs)),
    restore: vi.fn((id) => Promise.resolve({ id })),
  },
}

vi.mock('@/api/client', () => ({ api, ApiError: class ApiError extends Error {} }))

vi.mock('@/services/transition', () => ({
  TransitionLink: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useTransition: () => ({ navigate: vi.fn(), phase: 'idle', busy: false }),
}))

let canValue = true
vi.mock('@/services/auth', () => ({
  useAuth: () => ({ can: () => canValue }),
}))

let ActivityFeed, Trash

beforeEach(async () => {
  vi.clearAllMocks()
  canValue = true
  ;({ default: ActivityFeed } = await import('@/features/activity/ActivityFeed'))
  ;({ default: Trash } = await import('@/features/activity/Trash'))
})

function withRouter(ui) {
  return <MemoryRouter>{ui}</MemoryRouter>
}

describe('activity feed', () => {
  it('renders feed entries with translated actions and a link, no axe violations', async () => {
    const { container } = render(withRouter(<ActivityFeed />))
    await waitFor(() => expect(api.audit.feed).toHaveBeenCalled())
    expect(await screen.findByText('creó un proyecto')).toBeInTheDocument()
    expect(screen.getByText('restauró un catálogo')).toBeInTheDocument()
    const links = screen.getAllByRole('link', { name: /abrir objeto relacionado|open related/i })
    expect(links[0]).toHaveAttribute('href', '/app/proyectos/7')
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('hides the feed when audit:view is not granted', async () => {
    canValue = false
    render(withRouter(<ActivityFeed />))
    await waitFor(() => {})
    expect(api.audit.feed).not.toHaveBeenCalled()
  })
})

describe('trash / restore', () => {
  it('lists deleted projects and catalogs with no axe violations', async () => {
    const { container } = render(withRouter(<Trash />))
    await waitFor(() => expect(api.projects.listDeleted).toHaveBeenCalled())
    expect(await screen.findByText('Cliente Borrado')).toBeInTheDocument()
    expect(screen.getByText('Catálogo Borrado')).toBeInTheDocument()
    const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
    expect(results).toHaveNoViolations()
  })

  it('restores a project after confirming', async () => {
    render(withRouter(<Trash />))
    await waitFor(() => expect(api.projects.listDeleted).toHaveBeenCalled())
    const restoreBtn = await screen.findByRole('button', { name: /restaurar proyecto cliente borrado|restore project/i })
    fireEvent.click(restoreBtn)
    const accept = await screen.findByRole('button', { name: /^restaurar$|^restore$/i })
    fireEvent.click(accept)
    await waitFor(() => expect(api.projects.restore).toHaveBeenCalledWith(11))
  })
})

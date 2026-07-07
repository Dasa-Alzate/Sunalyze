import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const proyecto = { id: 7, cliente: 'ACME Solar', direccion: 'Calle Mayor 1', estado: 'diseno', kwp: 5.4, updated_at: new Date().toISOString() }

const api = {
  projects: {
    list: vi.fn(() => Promise.resolve([])),
    duplicate: vi.fn(() => Promise.resolve({})),
    remove: vi.fn(() => Promise.resolve({})),
  },
}

vi.mock('@/api/client', () => ({ api, csrfToken: () => 'tok' }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))
vi.mock('@/services/export', () => ({ exportRows: () => {} }))
vi.mock('@/services/auth', () => ({ useAuth: () => ({ can: () => true, flag: () => false }) }))
vi.mock('@/features/notifications/PendingWorkPanel', () => ({ default: () => null }))

let Dashboard, ProjectList
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: Dashboard } = await import('@/features/dashboard/Dashboard'))
  ;({ default: ProjectList } = await import('@/features/projects/ProjectList'))
})

function renderAt(ui) {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={ui} />
        <Route path="/app/diseno" element={<div>sonda-creacion</div>} />
        <Route path="/app/proyectos" element={<div>sonda-proyectos</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Dashboard · onboarding con 0 proyectos', () => {
  it('muestra la tarjeta de bienvenida con los pasos y el CTA en lugar del dashboard', async () => {
    api.projects.list.mockResolvedValue([])
    renderAt(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Bienvenido a Sunalyze')).toBeInTheDocument())
    expect(screen.getByText('Crea un proyecto')).toBeInTheDocument()
    expect(screen.getByText('Elige los equipos')).toBeInTheDocument()
    expect(screen.getByText('Revisa el análisis')).toBeInTheDocument()
    expect(screen.getByText('Genera la memoria')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Crear tu primer proyecto/ })).toBeInTheDocument()
    expect(screen.queryByText('Proyectos activos')).not.toBeInTheDocument()
    expect(screen.queryByText('Proyectos recientes')).not.toBeInTheDocument()
  })

  it('el CTA navega a la creación de proyecto', async () => {
    api.projects.list.mockResolvedValue([])
    renderAt(<Dashboard />)
    await waitFor(() => expect(screen.getByRole('button', { name: /Crear tu primer proyecto/ })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Crear tu primer proyecto/ }))
    await waitFor(() => expect(screen.getByText('sonda-creacion')).toBeInTheDocument())
  })

  it('con proyectos existentes renderiza el dashboard normal sin tarjeta de bienvenida', async () => {
    api.projects.list.mockResolvedValue([proyecto])
    renderAt(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Proyectos activos')).toBeInTheDocument())
    expect(screen.getByText('Proyectos recientes')).toBeInTheDocument()
    expect(screen.getByText('ACME Solar')).toBeInTheDocument()
    expect(screen.queryByText('Bienvenido a Sunalyze')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Crear tu primer proyecto/ })).not.toBeInTheDocument()
  })
})

describe('ProjectList · onboarding con 0 proyectos', () => {
  it('muestra el empty-state con mensaje y CTA y navega al crear', async () => {
    api.projects.list.mockResolvedValue([])
    renderAt(<ProjectList />)
    await waitFor(() => expect(screen.getByText('Aún no hay proyectos')).toBeInTheDocument())
    expect(screen.getByText(/Crea tu primer proyecto: de coordenadas a memoria técnica/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Crear tu primer proyecto/ }))
    await waitFor(() => expect(screen.getByText('sonda-creacion')).toBeInTheDocument())
  })

  it('con proyectos existentes renderiza la tabla normal', async () => {
    api.projects.list.mockResolvedValue([proyecto])
    renderAt(<ProjectList />)
    await waitFor(() => expect(screen.getByText('ACME Solar')).toBeInTheDocument())
    expect(screen.getByText('Calle Mayor 1')).toBeInTheDocument()
    expect(screen.queryByText('Aún no hay proyectos')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Crear tu primer proyecto/ })).not.toBeInTheDocument()
  })
})

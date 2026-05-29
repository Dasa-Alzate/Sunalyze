import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { axe } from 'vitest-axe'

const installations = [
  { id: 1, project_id: 10, cliente: 'ACME Solar', status: 'operativa', warranty_until: '2031-01-01', maintenance_count: 2, incident_count: 1, reading_count: 3 },
  { id: 2, project_id: 11, cliente: 'Beta Energía', status: 'incidencia', warranty_until: null, maintenance_count: 0, incident_count: 2, reading_count: 0 },
]

const performance = {
  installation_id: 1,
  expected_annual_kwh: 8200,
  actual_total_kwh: 6150,
  reading_count: 3,
  ratio: 0.75,
  method: 'manual_readings_v1',
  method_note: 'Suma de lecturas manuales frente al baseline esperado.',
}

const detail = {
  id: 1,
  project_id: 10,
  cliente: 'ACME Solar',
  status: 'operativa',
  commissioned_at: '2026-01-15',
  warranty_until: '2031-01-01',
  performance,
  maintenance: [
    { id: 100, kind: 'preventivo', status: 'programada', scheduled_at: '2026-07-01', done_at: null, technician: 'Lucía', notes: 'Revisión anual' },
  ],
  incidents: [
    { id: 200, title: 'Inversor sin comunicación', severity: 'alta', status: 'abierta', opened_at: '2026-06-01', resolved_at: null, description: 'Sin datos desde ayer' },
  ],
  readings: [{ id: 300, period: '2026-05', actual_kwh: 720 }],
}

const api = {
  installations: {
    list: vi.fn(() => Promise.resolve(installations)),
    get: vi.fn(() => Promise.resolve(detail)),
    create: vi.fn(() => Promise.resolve({ id: 3 })),
    update: vi.fn(() => Promise.resolve({})),
    maintenance: { create: vi.fn(), update: vi.fn(), remove: vi.fn() },
    incidents: { create: vi.fn(), update: vi.fn(), remove: vi.fn() },
    readings: { create: vi.fn(), update: vi.fn(), remove: vi.fn() },
  },
  projects: { list: vi.fn(() => Promise.resolve([{ id: 12, cliente: 'Gamma' }])) },
}

vi.mock('@/api/client', () => ({ api, ApiError: class ApiError extends Error {} }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))

let InstallationsWorkspace, InstallationDetail, PerformancePanel, VisitDialog, IncidentDialog
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: InstallationsWorkspace } = await import('@/features/posventa/InstallationsWorkspace'))
  ;({ default: InstallationDetail } = await import('@/features/posventa/InstallationDetail'))
  ;({ default: PerformancePanel } = await import('@/features/posventa/PerformancePanel'))
  ;({ default: VisitDialog } = await import('@/features/posventa/VisitDialog'))
  ;({ default: IncidentDialog } = await import('@/features/posventa/IncidentDialog'))
})

describe('posventa frontend', () => {
  it('InstallationsWorkspace lists installations with status badges and no axe violations', async () => {
    const { container } = render(<InstallationsWorkspace />)
    await screen.findByText('ACME Solar')
    expect(screen.getByText('Beta Energía')).toBeInTheDocument()
    expect(screen.getByText('Operativa')).toBeInTheDocument()
    expect(screen.getByText('Incidencia')).toBeInTheDocument()
    expect(await axe(container)).toHaveNoViolations()
  })

  it('InstallationDetail renders header, tabs and no axe violations', async () => {
    const { container } = render(<InstallationDetail installationId={1} onBack={() => {}} />)
    await screen.findByRole('heading', { name: /ACME Solar/ })
    expect(screen.getByRole('tab', { name: /Mantenimiento/ })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Incidencias/ })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Rendimiento/ })).toBeInTheDocument()
    expect(await axe(container)).toHaveNoViolations()
  })

  it('PerformancePanel paints the ratio from a mock', () => {
    render(<PerformancePanel performance={performance} onAddReading={() => {}} />)
    expect(screen.getByRole('img', { name: /rendimiento real frente al esperado: 75/i })).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText(/cifra indicativa/i)).toBeInTheDocument()
  })

  it('PerformancePanel handles missing baseline gracefully', () => {
    render(<PerformancePanel performance={{ expected_annual_kwh: null, actual_total_kwh: 0, ratio: null, reading_count: 0 }} onAddReading={() => {}} />)
    expect(screen.getByRole('img', { name: /sin baseline esperado/i })).toBeInTheDocument()
  })

  it('VisitDialog has no axe violations', async () => {
    const { container } = render(<VisitDialog onClose={() => {}} onSubmit={() => {}} />)
    expect(screen.getByRole('dialog', { name: /programar visita/i })).toBeInTheDocument()
    expect(await axe(container)).toHaveNoViolations()
  })

  it('IncidentDialog has no axe violations', async () => {
    const { container } = render(<IncidentDialog onClose={() => {}} onSubmit={() => {}} />)
    expect(screen.getByRole('dialog', { name: /abrir incidencia/i })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByLabelText(/Severidad/)).toBeInTheDocument())
    expect(await axe(container)).toHaveNoViolations()
  })
})

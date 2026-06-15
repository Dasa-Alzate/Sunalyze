import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const templates = [
  { name: 'solar-basico', label: 'Solar básico' },
  { name: 'solar-con-baterias', label: 'Solar con baterías' },
  { name: 'solar-sin-fusibles', label: 'Solar sin fusibles' },
  { name: 'solar-con-fusibles', label: 'Solar con fusibles' },
  { name: 'cc-strings', label: 'Esquema CC (strings)' },
  { name: 'grid-connection', label: 'Conexión a red' },
  { name: 'full-system', label: 'Sistema completo' },
]
const panels = [{ id: 11, nombre: 'LONGi 550', power: 550, voc: 49.5, isc: 13.9 }]
const inverters = [{ id: 21, nombre: 'Fronius 5.0', power: 5, vmax: 1000, I_max_output: 24 }]
const project = { id: 5, cliente: 'ACME', panel_id: 11, inverter_id: 21, battery_id: 3 }

const api = {
  circuit: {
    templates: vi.fn(() => Promise.resolve(templates)),
    svgUrl: (template, params = {}) => {
      const qs = new URLSearchParams(params).toString()
      return `/api/circuit/${template}${qs ? `?${qs}` : ''}`
    },
  },
  panels: { list: vi.fn(() => Promise.resolve(panels)) },
  inverters: { list: vi.fn(() => Promise.resolve(inverters)) },
  projects: { get: vi.fn(() => Promise.resolve(project)) },
}

vi.mock('@/api/client', () => ({ api, csrfToken: () => 'tok' }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))

let CircuitDiagram
let fetchMock
beforeEach(async () => {
  vi.clearAllMocks()
  fetchMock = vi.fn(() => Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('<svg aria-hidden="true"></svg>') }))
  vi.stubGlobal('fetch', fetchMock)
  ;({ default: CircuitDiagram } = await import('@/features/design/CircuitDiagram'))
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/app/diagrama" element={<CircuitDiagram />} />
        <Route path="/app/diagrama/:id" element={<CircuitDiagram />} />
      </Routes>
    </MemoryRouter>,
  )
}

function fetchedTemplates() {
  return fetchMock.mock.calls.map(([url]) => url.split('?')[0])
}

async function expectNoViolations(container) {
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('CircuitDiagram · diagrama unifilar', () => {
  it('renders the view with no axe violations', async () => {
    const { container } = renderAt('/app/diagrama')
    await waitFor(() => expect(screen.getByLabelText('Plantilla')).toBeInTheDocument())
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    await expectNoViolations(container)
  })

  it('fills the template selector from templates() with 7 options', async () => {
    renderAt('/app/diagrama')
    const select = await screen.findByLabelText('Plantilla')
    expect(api.circuit.templates).toHaveBeenCalledTimes(1)
    expect(select.querySelectorAll('option')).toHaveLength(7)
    expect(screen.getByRole('option', { name: 'Solar con baterías' })).toBeInTheDocument()
  })

  it('exposes the preview as an accessible image', async () => {
    renderAt('/app/diagrama')
    expect(await screen.findByRole('img', { name: /esquema unifilar/i })).toBeInTheDocument()
  })

  it('changing the template changes the previewed template fetched', async () => {
    renderAt('/app/diagrama')
    const select = await screen.findByLabelText('Plantilla')
    await waitFor(() => expect(fetchedTemplates()).toContain('/api/circuit/solar-con-fusibles'))
    fireEvent.change(select, { target: { value: 'full-system' } })
    await waitFor(() => expect(fetchedTemplates()).toContain('/api/circuit/full-system'))
  })

  it('battery toggle selects the solar-con-baterias template', async () => {
    renderAt('/app/diagrama')
    const select = await screen.findByLabelText('Plantilla')
    const batteryToggle = screen.getByLabelText(/baterías/i)
    fireEvent.click(batteryToggle)
    await waitFor(() => expect(select.value).toBe('solar-con-baterias'))
    await waitFor(() => expect(fetchedTemplates()).toContain('/api/circuit/solar-con-baterias'))
  })

  it('fuses toggle off (no battery) selects solar-sin-fusibles', async () => {
    renderAt('/app/diagrama')
    const select = await screen.findByLabelText('Plantilla')
    const fusesToggle = screen.getByLabelText(/fusibles/i)
    fireEvent.click(fusesToggle)
    await waitFor(() => expect(select.value).toBe('solar-sin-fusibles'))
  })

  it('seeds params from the project panel/inverter and pre-selects battery', async () => {
    renderAt('/app/diagrama/5')
    const select = await screen.findByLabelText('Plantilla')
    await waitFor(() => expect(api.projects.get).toHaveBeenCalledWith(5))
    expect(select.value).toBe('solar-con-baterias')
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map(([url]) => url)
      expect(urls.some((u) => u.includes('panel_model=LONGi+550') && u.includes('has_battery=true'))).toBe(true)
    })
  })
})

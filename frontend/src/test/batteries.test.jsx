import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const batteries = [
  { id: 1, nombre: 'BYD HVS 5.1', capacity_kwh: 5.12, usable_kwh: 4.6, dod: 90, power_kw: 5, voltage: 51.2, technology: 'LiFePO4', round_trip_efficiency: 95, max_cycles: 6000, catalog_id: 9, catalog_nombre: 'Mis equipos', editable: true },
  { id: 2, nombre: 'Tesla Powerwall', capacity_kwh: 13.5, usable_kwh: 13.5, dod: 100, power_kw: 5, voltage: 50, technology: 'NMC', round_trip_efficiency: 90, max_cycles: 5000, catalog_id: 3, catalog_nombre: 'Oficial', editable: false },
]
const panels = [{ id: 11, nombre: 'LONGi 550', power: 550, voc: 49, vmax: 1000, y: 21 }]
const inverters = [{ id: 21, nombre: 'Fronius 5.0', power: 5, vmax: 1000, y: 98 }]
const catalogs = [{ id: 9, nombre: 'Mis equipos', own: true, counts: { panels: 0, inverters: 0, batteries: 1, wires: 0 } }]

const project = {
  id: 5, cliente: 'ACME', localidad: 'Alicante', necesidad: 5000, autoconsumo: 90,
  latitud: 38.3, longitud: -0.49, coplanar: false,
  panel_id: 11, inverter_id: 21, battery_id: 1, battery_quantity: 2, battery_nombre: 'BYD HVS 5.1',
  resultados: null,
}

const analysis = {
  total_field_power: 5.5, annual_production: 8200, cell_amount: 10,
  battery: {
    battery_id: 1, nombre: 'BYD HVS 5.1', quantity: 2,
    bank_usable_kwh: 9.2, bank_capacity_kwh: 10.24,
    recommended_usable_kwh: 8.5, recommended_capacity_kwh: 9.4,
    annual_battery_contribution_kwh: 1800, estimated_self_consumption_pct: 96.5,
    self_consumption_uplift_pct: 6.5, round_trip_efficiency: 0.95, dod: 0.9,
    daily_consumption_kwh: 13.7, daily_production_kwh: 22.5, daily_surplus_kwh: 8.8,
    method: 'daily_balance_v1', method_note: 'Estimacion por balance diario promediado (no simulacion horaria).',
  },
}
project.resultados = analysis

const api = {
  panels: { list: vi.fn(() => Promise.resolve(panels)), create: vi.fn(), update: vi.fn(), remove: vi.fn() },
  inverters: { list: vi.fn(() => Promise.resolve(inverters)), create: vi.fn(), update: vi.fn(), remove: vi.fn() },
  batteries: { list: vi.fn(() => Promise.resolve(batteries)), create: vi.fn(() => Promise.resolve({ id: 99 })), update: vi.fn(), remove: vi.fn() },
  wires: { list: vi.fn(() => Promise.resolve([])) },
  catalogs: { list: vi.fn(() => Promise.resolve(catalogs)) },
  marketplace: { list: vi.fn(() => Promise.resolve([])) },
  projects: { get: vi.fn(() => Promise.resolve(project)), update: vi.fn(() => Promise.resolve(project)), create: vi.fn(() => Promise.resolve(project)) },
  analyze: vi.fn(() => Promise.resolve(analysis)),
}

vi.mock('@/api/client', () => ({ api, csrfToken: () => 'tok', setApiErrorHandler: () => {} }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))
vi.mock('@/services/export', () => ({ exportRows: () => {} }))
vi.mock('@/services/geo-map', () => ({ GeoMap: () => null }))
vi.mock('@/services/auth', () => ({
  useAuth: () => ({ can: () => true, flag: () => false }),
}))

let EquipmentLibrary, Wizard
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: EquipmentLibrary } = await import('@/features/equipment/EquipmentLibrary'))
  ;({ default: Wizard } = await import('@/features/design/Wizard'))
})

async function expectNoViolations(container) {
  const results = await axe(container, { rules: { 'color-contrast': { enabled: false } } })
  expect(results).toHaveNoViolations()
}

describe('EquipmentLibrary · baterías', () => {
  it('muestra la pestaña de baterías y el formulario sin violaciones axe', async () => {
    const { container } = render(<MemoryRouter><EquipmentLibrary /></MemoryRouter>)
    await waitFor(() => expect(screen.getByRole('button', { name: /Baterías/ })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Baterías/ }))
    await waitFor(() => expect(api.batteries.list).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByText('BYD HVS 5.1')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Añadir batería/ }))
    expect(screen.getByLabelText(/Capacidad nominal/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Eficiencia ida y vuelta/)).toBeInTheDocument()
    await expectNoViolations(container)
  })

  it('crea una batería enviando los campos al backend', async () => {
    render(<MemoryRouter><EquipmentLibrary /></MemoryRouter>)
    await waitFor(() => expect(screen.getByRole('button', { name: /Baterías/ })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Baterías/ }))
    await waitFor(() => expect(screen.getByText('BYD HVS 5.1')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Añadir batería/ }))
    fireEvent.change(screen.getByLabelText(/Nombre/), { target: { value: 'Pylontech US5000' } })
    fireEvent.change(screen.getByLabelText(/Capacidad nominal/), { target: { value: '4.8' } })
    fireEvent.change(screen.getByLabelText(/Potencia \(kW\)/), { target: { value: '3.5' } })
    fireEvent.change(screen.getByLabelText(/Voltaje/), { target: { value: '48' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(api.batteries.create).toHaveBeenCalled())
    const body = api.batteries.create.mock.calls[0][0]
    expect(body.nombre).toBe('Pylontech US5000')
    expect(body.capacity_kwh).toBe(4.8)
    expect(body.power_kw).toBe(3.5)
    expect(body.voltage).toBe(48)
  })
})

function renderWizard() {
  return render(
    <MemoryRouter initialEntries={['/app/diseno/5']}>
      <Routes>
        <Route path="/app/diseno/:id" element={<Wizard />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Wizard · batería', () => {
  it('precarga la batería del proyecto y la cantidad', async () => {
    renderWizard()
    await waitFor(() => expect(api.batteries.list).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: /Equipos/ }))
    await waitFor(() => expect(screen.getByLabelText(/Cantidad de baterías/)).toBeInTheDocument())
    expect(screen.getByLabelText(/Cantidad de baterías/)).toHaveValue(2)
  })

  it('el selector de batería no produce violaciones axe', async () => {
    const { container } = renderWizard()
    await waitFor(() => expect(api.batteries.list).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: /Equipos/ }))
    await waitFor(() => expect(screen.getByText(/déjala vacía/)).toBeInTheDocument())
    await expectNoViolations(container)
  })

  it('muestra el bloque de análisis de batería con aporte anual y autoconsumo', async () => {
    renderWizard()
    await waitFor(() => expect(api.projects.get).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: /Análisis/ }))
    await waitFor(() => expect(screen.getByText(/Aporte anual batería/)).toBeInTheDocument())
    expect(screen.getByText(/Autoconsumo estimado/)).toBeInTheDocument()
    expect(screen.getByText(/no simulacion horaria/)).toBeInTheDocument()
  })

  it('envía battery_id y battery_quantity al guardar', async () => {
    renderWizard()
    await waitFor(() => expect(api.projects.get).toHaveBeenCalled())
    await waitFor(() => expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(api.projects.update).toHaveBeenCalled())
    const body = api.projects.update.mock.calls[0][1]
    expect(body.battery_id).toBe(1)
    expect(body.battery_quantity).toBe(2)
  })
})

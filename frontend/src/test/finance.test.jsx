import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { axe } from 'vitest-axe'

const results = {
  inputs: { production_kwh_year: 8200, self_consumption_ratio: 0.65, lifetime_years: 25, discount_rate: 0.04 },
  capex: { gross_eur: 9000, with_vat_eur: 10890, incentive_reduction_eur: 3000, net_eur: 7890, financed_eur: 0, initial_investment_eur: 7890 },
  annual_saving_year1_eur: 1230,
  incentives: {
    items: [
      { kind: 'capex_reduction', amount: 3000, year: 1, label: 'Deducción IRPF (40%)' },
      { kind: 'cashflow', amount: 100, year: 1, label: 'Bonificación IBI' },
    ],
    total_eur: 3100,
  },
  metrics: {
    payback_simple_years: 6.4, payback_discounted_years: 7.8, roi: 2.1, irr: 0.142,
    npv_eur: 14200, lcoe_eur_kwh: 0.062, co2_avoided_year1_kg: 2050, co2_avoided_lifetime_kg: 48000,
  },
  cashflow: [
    { year: 1, cashflow_eur: 1230, discounted_cashflow_eur: 1182, co2_avoided_kg: 2050 },
    { year: 2, cashflow_eur: 1250, discounted_cashflow_eur: 1155, co2_avoided_kg: 2040 },
    { year: 3, cashflow_eur: 1270, discounted_cashflow_eur: 1129, co2_avoided_kg: 2030 },
    { year: 4, cashflow_eur: 1290, discounted_cashflow_eur: 1102, co2_avoided_kg: 2020 },
    { year: 5, cashflow_eur: 1310, discounted_cashflow_eur: 1077, co2_avoided_kg: 2010 },
    { year: 6, cashflow_eur: 1330, discounted_cashflow_eur: 1051, co2_avoided_kg: 2000 },
    { year: 7, cashflow_eur: 1350, discounted_cashflow_eur: 1026, co2_avoided_kg: 1990 },
  ],
}

const scenarios = [
  { id: 1, name: 'Contado', is_default: true, assumptions: { capex_total: 9000 }, results },
  { id: 2, name: 'Financiado', is_default: false, assumptions: { capex_total: 9000, financing: { amount: 5000, interest_rate: 0.05, term_years: 10 } }, results: { ...results, metrics: { ...results.metrics, payback_simple_years: 9.1 } } },
]

const financeCatalog = [
  { entity: 'project', label: 'Proyecto', vars: [{ path: 'project.cliente', label: 'Cliente', tipo: 'text' }] },
  { entity: 'finance', label: 'Finanzas', vars: [
    { path: 'finance.payback_years', label: 'Payback simple (años)', tipo: 'number' },
    { path: 'finance.npv', label: 'VAN (€)', tipo: 'number' },
  ] },
]

const api = {
  finance: {
    compute: vi.fn(() => Promise.resolve(results)),
    scenarios: vi.fn(() => Promise.resolve(scenarios)),
    createScenario: vi.fn(() => Promise.resolve({ id: 3 })),
    removeScenario: vi.fn(() => Promise.resolve({ ok: true })),
  },
  projects: { list: vi.fn(() => Promise.resolve([{ id: 5, cliente: 'ACME' }])) },
  templates: {
    list: vi.fn(() => Promise.resolve([])),
    bank: vi.fn(() => Promise.resolve([])),
    preview: vi.fn(() => Promise.resolve({ html: '' })),
    variables: vi.fn(() => Promise.resolve(financeCatalog)),
  },
}

vi.mock('@/api/client', () => ({ api, ApiError: class ApiError extends Error {}, csrfToken: () => 'tok' }))
vi.mock('@/services/toast', () => ({ toast: () => {} }))

let AssumptionsForm, ResultsDashboard, ScenarioComparison, VariablePicker
beforeEach(async () => {
  vi.clearAllMocks()
  ;({ default: AssumptionsForm } = await import('@/features/finance/AssumptionsForm'))
  ;({ default: ResultsDashboard } = await import('@/features/finance/ResultsDashboard'))
  ;({ default: ScenarioComparison } = await import('@/features/finance/ScenarioComparison'))
  ;({ default: VariablePicker } = await import('@/features/templates/VariablePicker'))
})

describe('finance frontend', () => {
  it('AssumptionsForm has no axe violations', async () => {
    const { container } = render(<AssumptionsForm form={{
      capexMode: 'total', capex_total: 9000, iva_pct: 0.21, tariff_eur_kwh: 0.15,
      annual_consumption_kwh: '', autoRatio: true, self_consumption_ratio: 0.65,
      surplus_price_eur_kwh: 0.06, lifetime_years: 25, discount_rate: 0.04,
      tariff_escalation_pct: 0.025, panel_degradation_pct: 0.005, om_cost_eur_year: 0,
      emission_factor_kg_kwh: 0.25, financed: false, apply_subsidies: true, ccaa: 'madrid', municipio: 'madrid',
    }} onChange={() => {}} />)
    expect(await axe(container)).toHaveNoViolations()
  })

  it('ResultsDashboard renders KPIs from a results mock', () => {
    render(<ResultsDashboard results={results} />)
    expect(screen.getByText('Payback simple')).toBeInTheDocument()
    expect(screen.getByText('TIR')).toBeInTheDocument()
    expect(screen.getByText('VAN')).toBeInTheDocument()
    expect(screen.getByText('LCOE')).toBeInTheDocument()
    expect(screen.getByText('14.200')).toBeInTheDocument()
    expect(screen.getByText('14,2')).toBeInTheDocument()
    expect(screen.getByText('Deducción IRPF (40%)')).toBeInTheDocument()
    expect(screen.getByText(/mejor caso indicativo/i)).toBeInTheDocument()
  })

  it('ResultsDashboard cashflow chart is accessible with role img', () => {
    render(<ResultsDashboard results={results} />)
    expect(screen.getByRole('img', { name: /flujo de caja acumulado/i })).toBeInTheDocument()
  })

  it('ResultsDashboard has no axe violations', async () => {
    const { container } = render(<ResultsDashboard results={results} />)
    expect(await axe(container)).toHaveNoViolations()
  })

  it('ScenarioComparison shows columns per scenario and no axe violations', async () => {
    const { container } = render(<ScenarioComparison scenarios={scenarios} />)
    expect(screen.getByText('Contado')).toBeInTheDocument()
    expect(screen.getByText('Financiado')).toBeInTheDocument()
    expect(screen.getByText('VAN (€)')).toBeInTheDocument()
    expect(await axe(container)).toHaveNoViolations()
  })

  it('VariablePicker exposes finance.* variables for propuesta_comercial', async () => {
    render(<VariablePicker kind="propuesta_comercial" onInsert={() => {}} onClose={() => {}} />)
    await waitFor(() => expect(api.templates.variables).toHaveBeenCalledWith('propuesta_comercial'))
    const entitySelect = await screen.findByLabelText('Entidad')
    expect([...entitySelect.options].some((o) => o.textContent === 'Finanzas')).toBe(true)
    fireEvent.change(entitySelect, { target: { value: 'finance' } })
    const propSelect = screen.getByLabelText('Propiedad')
    await waitFor(() => expect([...propSelect.options].some((o) => /VAN/.test(o.textContent))).toBe(true))
  })
})

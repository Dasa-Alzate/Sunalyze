export const DEFAULTS = {
  capexMode: 'total',
  capex_total: '',
  capex_equipment: '',
  capex_labor: '',
  capex_legalization: '',
  iva_pct: 0.21,
  tariff_eur_kwh: 0.15,
  annual_consumption_kwh: '',
  autoRatio: true,
  self_consumption_ratio: 0.65,
  surplus_price_eur_kwh: 0.06,
  lifetime_years: 25,
  discount_rate: 0.04,
  tariff_escalation_pct: 0.025,
  panel_degradation_pct: 0.005,
  om_cost_eur_year: 0,
  emission_factor_kg_kwh: 0.25,
  financed: false,
  financing_amount: '',
  financing_interest_rate: 0.05,
  financing_term_years: 10,
  apply_subsidies: false,
  ccaa: '',
  municipio: '',
}

export const CCAA_OPTIONS = [
  { value: '', label: 'Solo nacional (IRPF + Next Gen)' },
  { value: 'andalucia', label: 'Andalucía' },
  { value: 'cataluna', label: 'Cataluña' },
  { value: 'comunidad valenciana', label: 'Comunidad Valenciana' },
  { value: 'comunidad de madrid', label: 'Comunidad de Madrid' },
]

export const MUNICIPIO_OPTIONS = [
  { value: '', label: 'Sin bonificación municipal' },
  { value: 'madrid', label: 'Madrid (IBI + ICIO)' },
  { value: 'barcelona', label: 'Barcelona (IBI + ICIO)' },
  { value: 'valencia', label: 'Valencia (IBI + ICIO)' },
]

export const INCENTIVE_KIND_LABELS = {
  capex_reduction: 'Reduce CAPEX',
  cashflow: 'Aporte anual',
}

function toNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  const n = Number(value)
  return Number.isNaN(n) ? null : n
}

export function formToAssumptions(form) {
  const assumptions = {
    iva_pct: Number(form.iva_pct),
    tariff_eur_kwh: Number(form.tariff_eur_kwh),
    surplus_price_eur_kwh: Number(form.surplus_price_eur_kwh),
    lifetime_years: Number(form.lifetime_years),
    discount_rate: Number(form.discount_rate),
    tariff_escalation_pct: Number(form.tariff_escalation_pct),
    panel_degradation_pct: Number(form.panel_degradation_pct),
    om_cost_eur_year: Number(form.om_cost_eur_year) || 0,
    emission_factor_kg_kwh: Number(form.emission_factor_kg_kwh),
  }

  if (form.capexMode === 'total') {
    assumptions.capex_total = toNumber(form.capex_total)
  } else {
    assumptions.capex_equipment = toNumber(form.capex_equipment)
    assumptions.capex_labor = toNumber(form.capex_labor)
    assumptions.capex_legalization = toNumber(form.capex_legalization)
  }

  const consumption = toNumber(form.annual_consumption_kwh)
  if (consumption !== null) assumptions.annual_consumption_kwh = consumption

  if (!form.autoRatio) {
    assumptions.self_consumption_ratio = Number(form.self_consumption_ratio)
  }

  if (form.financed) {
    assumptions.financing = {
      amount: toNumber(form.financing_amount) || 0,
      interest_rate: Number(form.financing_interest_rate) || 0,
      term_years: Number(form.financing_term_years) || 0,
    }
  }

  return assumptions
}

export function formToComputeBody(form) {
  const body = {
    assumptions: formToAssumptions(form),
    apply_subsidies: !!form.apply_subsidies,
  }
  if (form.apply_subsidies) {
    if (form.ccaa) body.ccaa = form.ccaa
    if (form.municipio) body.municipio = form.municipio
  }
  if (!form.autoRatio) body.self_consumption_ratio = Number(form.self_consumption_ratio)
  return body
}

export function hasCapex(form) {
  if (form.capexMode === 'total') return toNumber(form.capex_total) !== null
  return (
    toNumber(form.capex_equipment) !== null ||
    toNumber(form.capex_labor) !== null ||
    toNumber(form.capex_legalization) !== null
  )
}

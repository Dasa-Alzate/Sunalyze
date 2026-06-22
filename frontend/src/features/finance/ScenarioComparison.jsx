import { Icon, Badge } from '@/shared/ui'
import { num, int, pct } from '@/shared/format'

const ROWS = [
  { label: 'CAPEX neto (€)', get: (r) => num(r?.capex?.net_eur, 0) },
  { label: 'Inversión inicial (€)', get: (r) => num(r?.capex?.initial_investment_eur, 0) },
  { label: 'Payback simple (años)', get: (r) => num(r?.metrics?.payback_simple_years, 1) },
  { label: 'Payback descontado (años)', get: (r) => num(r?.metrics?.payback_discounted_years, 1) },
  { label: 'TIR (%)', get: (r) => pct(r?.metrics?.irr, 1) },
  { label: 'VAN (€)', get: (r) => num(r?.metrics?.npv_eur, 0) },
  { label: 'LCOE (€/kWh)', get: (r) => num(r?.metrics?.lcoe_eur_kwh, 3) },
  { label: 'ROI (%)', get: (r) => pct(r?.metrics?.roi, 0) },
  { label: 'Ahorro anual año 1 (€)', get: (r) => num(r?.annual_saving_year1_eur, 0) },
  { label: 'Incentivos (€)', get: (r) => num(r?.incentives?.total_eur, 0) },
  { label: 'CO₂ evitado vida útil (kg)', get: (r) => int(r?.metrics?.co2_avoided_lifetime_kg) },
]

export default function ScenarioComparison({ scenarios }) {
  const list = scenarios || []
  if (list.length < 2) {
    return (
      <p style={{ color: 'var(--text-muted)' }}>
        Guarda al menos dos escenarios (p. ej. contado vs financiado) para compararlos lado a lado.
      </p>
    )
  }

  return (
    <div className="finance-comparison" style={{ overflowX: 'auto' }}>
      <table className="sun-table">
        <caption className="sr-only">Comparación de escenarios financieros guardados</caption>
        <thead>
          <tr>
            <th scope="col">Métrica</th>
            {list.map((s) => (
              <th scope="col" key={s.id}>
                {s.name}
                {s.is_default && <Badge tone="neutral" icon="star">Por defecto</Badge>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              {list.map((s) => (
                <td key={s.id}>{row.get(s.results)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

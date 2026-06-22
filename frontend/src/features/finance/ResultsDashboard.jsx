import { Metric, Icon } from '@/shared/ui'
import { num, int, pct } from '@/shared/format'
import CashflowChart from './CashflowChart'
import IncentivesBreakdown from './IncentivesBreakdown'

export default function ResultsDashboard({ results }) {
  if (!results) return null
  const m = results.metrics || {}
  const capex = results.capex || {}

  return (
    <div className="finance-dashboard">
      <div className="sun-section-title">
        <Icon name="bar-chart-3" size={15} />
        Resultados del estudio
      </div>
      <div className="finance-kpis" role="group" aria-label="Indicadores financieros">
        <Metric label="Payback simple" value={num(m.payback_simple_years, 1)} unit="años" />
        <Metric label="Payback descontado" value={num(m.payback_discounted_years, 1)} unit="años" />
        <Metric label="TIR" value={pct(m.irr, 1)} unit="%" />
        <Metric label="VAN" value={num(m.npv_eur, 0)} unit="€" />
        <Metric label="LCOE" value={num(m.lcoe_eur_kwh, 3)} unit="€/kWh" />
        <Metric label="ROI" value={pct(m.roi, 0)} unit="%" />
        <Metric label="CAPEX neto" value={num(capex.net_eur, 0)} unit="€" />
        <Metric label="Ahorro anual (año 1)" value={num(results.annual_saving_year1_eur, 0)} unit="€" />
        <Metric label="CO₂ evitado (año 1)" value={int(m.co2_avoided_year1_kg)} unit="kg" />
        <Metric label="CO₂ evitado (vida útil)" value={int(m.co2_avoided_lifetime_kg)} unit="kg" />
      </div>

      <CashflowChart results={results} />
      <IncentivesBreakdown incentives={results.incentives} />
    </div>
  )
}

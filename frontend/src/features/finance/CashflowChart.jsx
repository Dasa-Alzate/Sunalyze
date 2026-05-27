import { useId, useState } from 'react'
import { Icon, Btn } from '@/shared/ui'
import { num } from '@/shared/format'
import { buildChartGeometry, cumulativeSeries } from './cashflow'

export default function CashflowChart({ results }) {
  const titleId = useId()
  const descId = useId()
  const [showTable, setShowTable] = useState(false)
  const geo = buildChartGeometry(results)
  const series = cumulativeSeries(results)

  if (!geo) {
    return <p style={{ color: 'var(--text-muted)' }}>No hay datos de flujo de caja.</p>
  }

  const pb = geo.paybackYear
  const description = pb !== null
    ? `Flujo de caja acumulado a lo largo de ${geo.maxYear} años. La inversión se recupera en el año ${pb}.`
    : `Flujo de caja acumulado a lo largo de ${geo.maxYear} años. La inversión no se recupera dentro de la vida útil.`

  return (
    <div className="finance-chart">
      <div className="sun-section-title">
        <Icon name="trending-up" size={15} />
        Flujo de caja acumulado
        <Btn
          variant="secondary"
          size="sm"
          icon={showTable ? 'line-chart' : 'table'}
          onClick={() => setShowTable((v) => !v)}
          style={{ marginLeft: 'auto' }}
        >
          {showTable ? 'Ver gráfico' : 'Ver tabla'}
        </Btn>
      </div>

      {showTable ? (
        <div style={{ overflowX: 'auto' }}>
          <table className="sun-table">
            <caption className="sr-only">{description}</caption>
            <thead>
              <tr>
                <th scope="col">Año</th>
                <th scope="col">Acumulado (€)</th>
              </tr>
            </thead>
            <tbody>
              {series.map((p) => (
                <tr key={p.year}>
                  <td>{p.year}</td>
                  <td style={{ color: p.value >= 0 ? 'var(--state-valid)' : 'var(--danger)' }}>{num(p.value, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <svg
          viewBox={`0 0 ${geo.width} ${geo.height}`}
          width="100%"
          role="img"
          aria-labelledby={`${titleId} ${descId}`}
          style={{ display: 'block', maxWidth: '100%' }}
        >
          <title id={titleId}>Flujo de caja acumulado</title>
          <desc id={descId}>{description}</desc>
          <line
            x1={geo.pad} y1={geo.baseY} x2={geo.width - geo.pad} y2={geo.baseY}
            stroke="var(--border-strong)" strokeWidth="1" strokeDasharray="4 4"
          />
          <path d={geo.area} fill="var(--green-100)" opacity="0.6" />
          <path d={geo.line} fill="none" stroke="var(--green-600)" strokeWidth="2.5" />
          {geo.paybackX !== null && (
            <g>
              <line
                x1={geo.paybackX} y1={geo.pad} x2={geo.paybackX} y2={geo.height - geo.pad}
                stroke="var(--state-warn)" strokeWidth="1.5" strokeDasharray="5 3"
              />
              <text
                x={geo.paybackX + 4} y={geo.pad + 12}
                fontSize="11" fill="var(--state-warn)"
              >
                Payback año {pb}
              </text>
            </g>
          )}
          {geo.points.map((p) => (
            <circle key={p.year} cx={p.cx} cy={p.cy} r="2.5" fill="var(--green-700)" />
          ))}
        </svg>
      )}
    </div>
  )
}

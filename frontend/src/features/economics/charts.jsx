const SERIES_COLORS = ['var(--green-500)', 'var(--blue-500)', 'var(--amber-500)', 'var(--red-500)']
const GRID = 'var(--border-subtle)'
const INK = 'var(--text-muted)'
const INK_SOFT = 'var(--text-subtle)'

const eur0 = (v) => `${Math.round(v).toLocaleString('es-ES')} €`

function Legend({ items }) {
  return (
    <div className="eco-legend">
      {items.map((it, i) => (
        <span key={it} className="eco-legend__item">
          <span className="eco-legend__dot" style={{ background: SERIES_COLORS[i] }} />
          {it}
        </span>
      ))}
    </div>
  )
}

function yTicks(max) {
  const step = max / 4
  return [1, 2, 3, 4].map((i) => i * step)
}

export function SweepChart({ sweep }) {
  const W = 580
  const H = 280
  const M = { top: 18, right: 130, bottom: 34, left: 56 }
  const kwp = sweep.kwp
  const maxY = Math.max(sweep.techo, ...sweep.series.flatMap((s) => s.ahorros)) * 1.08
  const x = (v) => M.left + ((v - kwp[0]) / (kwp[kwp.length - 1] - kwp[0])) * (W - M.left - M.right)
  const y = (v) => H - M.bottom - (v / maxY) * (H - M.top - M.bottom)
  const labelYs = sweep.series
    .map((s, i) => ({ i, y: y(s.ahorros[s.ahorros.length - 1]) }))
    .sort((a, b) => a.y - b.y)
  for (let k = 1; k < labelYs.length; k += 1) {
    if (labelYs[k].y - labelYs[k - 1].y < 12) labelYs[k].y = labelYs[k - 1].y + 12
  }
  const labelY = new Map(labelYs.map((l) => [l.i, l.y]))

  return (
    <div>
      <Legend items={sweep.series.map((s) => s.nombre)} />
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label="Ahorro anual según potencia fotovoltaica, por batería">
        {yTicks(maxY).map((t) => (
          <g key={t}>
            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill={INK_SOFT}>{eur0(t)}</text>
          </g>
        ))}
        <line x1={M.left} x2={W - M.right} y1={y(sweep.techo)} y2={y(sweep.techo)} stroke={INK_SOFT} strokeWidth="1.5" strokeDasharray="5 4" />
        <text x={W - M.right - 4} y={y(sweep.techo) - 5} textAnchor="end" fontSize="10" fill={INK}>
          Ahorro máximo (factura actual {eur0(sweep.techo)})
        </text>
        {kwp.map((k) => (
          <text key={k} x={x(k)} y={H - M.bottom + 16} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{k}</text>
        ))}
        <text x={(M.left + W - M.right) / 2} y={H - 4} textAnchor="middle" fontSize="10" fill={INK}>Potencia fotovoltaica (kWp)</text>
        {sweep.series.map((s, si) => (
          <g key={s.nombre}>
            <polyline
              points={s.ahorros.map((a, i) => `${x(kwp[i])},${y(a)}`).join(' ')}
              fill="none" stroke={SERIES_COLORS[si]} strokeWidth="2" strokeLinejoin="round"
            />
            {s.ahorros.map((a, i) => (
              <circle key={i} cx={x(kwp[i])} cy={y(a)} r="4" fill={SERIES_COLORS[si]} stroke="var(--surface-card)" strokeWidth="2">
                <title>{`${s.nombre} · ${kwp[i]} kWp → ${eur0(a)}/año`}</title>
              </circle>
            ))}
            <text x={x(kwp[kwp.length - 1]) + 8} y={labelY.get(si) + 3} fontSize="10" fill={INK}>
              {s.nombre.length > 18 ? `${s.nombre.slice(0, 17)}…` : s.nombre}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}

export function PaybackChart({ scenarios }) {
  const rows = scenarios.escenarios.filter((r) => r.battery_id !== null && r.payback_bateria_anios != null)
  const sinPrecio = scenarios.escenarios.filter((r) => r.battery_id !== null && r.payback_bateria_anios == null)
  if (!rows.length) {
    return (
      <p className="eco-panel__note">
        No hay baterías con precio y aporte positivo para estimar el payback: pon <strong>precio unitario</strong> a las baterías en la biblioteca de equipos.
      </p>
    )
  }
  const W = 580
  const H = 280
  const M = { top: 16, right: 24, bottom: 36, left: 56 }
  const maxX = Math.max(...rows.map((r) => r.payback_bateria_anios)) * 1.15
  const maxY = Math.max(...rows.map((r) => r.ahorro_anual)) * 1.15
  const x = (v) => M.left + (v / maxX) * (W - M.left - M.right)
  const y = (v) => H - M.bottom - (v / maxY) * (H - M.top - M.bottom)

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label="Ahorro anual frente a años de payback de cada batería">
        {yTicks(maxY).map((t) => (
          <g key={t}>
            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill={INK_SOFT}>{eur0(t)}</text>
          </g>
        ))}
        {yTicks(maxX).map((t) => (
          <text key={t} x={x(t)} y={H - M.bottom + 16} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{t.toFixed(1)}</text>
        ))}
        <text x={(M.left + W - M.right) / 2} y={H - 4} textAnchor="middle" fontSize="10" fill={INK}>Payback de la batería (años)</text>
        {rows.map((r, i) => (
          <g key={r.battery_id}>
            <circle cx={x(r.payback_bateria_anios)} cy={y(r.ahorro_anual)} r="6" fill={SERIES_COLORS[i % SERIES_COLORS.length]} stroke="var(--surface-card)" strokeWidth="2">
              <title>{`${r.nombre} · payback ${r.payback_bateria_anios.toLocaleString('es-ES')} años → ${eur0(r.ahorro_anual)}/año`}</title>
            </circle>
            <text x={x(r.payback_bateria_anios)} y={y(r.ahorro_anual) - 10} textAnchor="middle" fontSize="9" fill={INK}>
              {r.nombre.length > 18 ? `${r.nombre.slice(0, 17)}…` : r.nombre}
            </text>
          </g>
        ))}
      </svg>
      <p className="eco-panel__note">Arriba a la izquierda: más ahorro y antes amortizada.{sinPrecio.length > 0 && ` Sin precio: ${sinPrecio.map((r) => r.nombre).join(', ')}.`}</p>
    </div>
  )
}

const MESES = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

export function MonthlyBillChart({ antes, despues }) {
  const W = 580
  const H = 240
  const M = { top: 14, right: 12, bottom: 26, left: 52 }
  const maxY = Math.max(...antes.map((m) => m.factura_neta), 1) * 1.1
  const band = (W - M.left - M.right) / 12
  const bw = Math.min(16, (band - 8) / 2)
  const y = (v) => H - M.bottom - (v / maxY) * (H - M.top - M.bottom)

  return (
    <div>
      <div className="eco-legend">
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: 'var(--ink-400, #9aa0a6)' }} />Sin placas</span>
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: SERIES_COLORS[0] }} />Con el sistema</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label="Factura mensual antes y después del sistema">
        {yTicks(maxY).map((t) => (
          <g key={t}>
            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill={INK_SOFT}>{eur0(t)}</text>
          </g>
        ))}
        {antes.map((m, i) => {
          const cx = M.left + band * i + band / 2
          const d = despues[i]
          return (
            <g key={i}>
              <rect x={cx - bw - 1} y={y(m.factura_neta)} width={bw} height={Math.max(0, y(0) - y(m.factura_neta))} rx="3" fill="var(--ink-400, #9aa0a6)">
                <title>{`${MESES[i]} sin placas: ${m.factura_neta.toLocaleString('es-ES')} €`}</title>
              </rect>
              <rect x={cx + 1} y={y(d.factura_neta)} width={bw} height={Math.max(0, y(0) - y(d.factura_neta))} rx="3" fill={SERIES_COLORS[0]}>
                <title>{`${MESES[i]} con el sistema: ${d.factura_neta.toLocaleString('es-ES')} €`}</title>
              </rect>
              <text x={cx} y={H - M.bottom + 14} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{MESES[i]}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

const MESES_LARGOS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
const eur2 = (v) => `${v.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`

export function MonthlyBillTable({ antes, despues, totalAntes, totalDespues }) {
  return (
    <table className="sun-table eco-billtable">
      <thead>
        <tr>
          <th>Mes</th>
          <th style={{ textAlign: 'right' }}>Sin placas</th>
          <th style={{ textAlign: 'right' }}>Con el sistema</th>
          <th style={{ textAlign: 'right' }}>Ahorro</th>
        </tr>
      </thead>
      <tbody>
        {antes.map((m, i) => (
          <tr key={MESES_LARGOS[i]}>
            <td>{MESES_LARGOS[i]}</td>
            <td style={{ textAlign: 'right' }}>{eur2(m.factura_neta)}</td>
            <td style={{ textAlign: 'right' }}>{eur2(despues[i].factura_neta)}</td>
            <td style={{ textAlign: 'right' }}>{eur2(m.factura_neta - despues[i].factura_neta)}</td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <th>Total anual</th>
          <th style={{ textAlign: 'right' }}>{eur2(totalAntes)}</th>
          <th style={{ textAlign: 'right' }}>{eur2(totalDespues)}</th>
          <th style={{ textAlign: 'right' }}>{eur2(totalAntes - totalDespues)}</th>
        </tr>
      </tfoot>
    </table>
  )
}

function DayPanel({ title, data, maxY }) {
  const W = 280
  const H = 200
  const M = { top: 14, right: 8, bottom: 26, left: 34 }
  const x = (h) => M.left + (h / 23) * (W - M.left - M.right)
  const y = (v) => H - M.bottom - (v / maxY) * (H - M.top - M.bottom)
  const area = `${x(0)},${y(0)} ${data.produccion.map((v, h) => `${x(h)},${y(v)}`).join(' ')} ${x(23)},${y(0)}`

  return (
    <div className="eco-daypanel">
      <span className="eco-daypanel__title">{title}</span>
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label={`Consumo y producción del ${title.toLowerCase()}`}>
        {yTicks(maxY).slice(1, 4).map((t) => (
          <line key={t} x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
        ))}
        <polygon points={area} fill="var(--amber-500)" opacity="0.15" />
        <polyline points={data.produccion.map((v, h) => `${x(h)},${y(v)}`).join(' ')} fill="none" stroke="var(--amber-500)" strokeWidth="2" />
        <polyline points={data.consumo.map((v, h) => `${x(h)},${y(v)}`).join(' ')} fill="none" stroke="var(--blue-500)" strokeWidth="2" />
        {[0, 6, 12, 18, 23].map((h) => (
          <text key={h} x={x(h)} y={H - M.bottom + 14} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{h}h</text>
        ))}
        <text x={M.left - 4} y={y(maxY * 0.75) + 3} textAnchor="end" fontSize="9" fill={INK_SOFT}>{(maxY * 0.75).toFixed(1)}</text>
      </svg>
    </div>
  )
}

export function DayTypeChart({ diaTipo }) {
  const maxY = Math.max(
    ...diaTipo.invierno.consumo, ...diaTipo.invierno.produccion,
    ...diaTipo.verano.consumo, ...diaTipo.verano.produccion,
  ) * 1.1
  return (
    <div>
      <div className="eco-legend">
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: 'var(--blue-500)' }} />Consumo (kWh/h)</span>
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: 'var(--amber-500)' }} />Producción solar (kWh/h)</span>
      </div>
      <div className="eco-daytype">
        <DayPanel title="Solsticio de invierno (21 dic)" data={diaTipo.invierno} maxY={maxY} />
        <DayPanel title="Solsticio de verano (21 jun)" data={diaTipo.verano} maxY={maxY} />
      </div>
      <p className="eco-panel__note">El hueco entre la curva azul y la mancha ámbar es lo que la batería puede desplazar.</p>
    </div>
  )
}

const FLOW_MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

export function MonthlyEnergyFlowChart({ flow }) {
  const W = 760
  const H = 320
  const M = { top: 18, right: 14, bottom: 42, left: 54 }
  const plotWidth = W - M.left - M.right
  const baseline = H - M.bottom
  const productionTotal = flow.production
  const maxY = Math.max(1, ...flow.consumption, ...productionTotal) * 1.08
  const y = (value) => baseline - (value / maxY) * (baseline - M.top)
  const groupWidth = plotWidth / FLOW_MONTHS.length
  const barWidth = Math.min(19, groupWidth * 0.33)
  const colors = {
    consumption: 'var(--red-500)',
    direct: 'var(--green-500)',
    battery: 'var(--blue-500)',
    export: 'var(--amber-500)',
  }

  return (
    <div>
      <div className="eco-legend" aria-label="Leyenda de energía mensual">
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: colors.consumption }} />Consumo</span>
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: colors.direct }} />Autoconsumo directo</span>
        {flow.has_battery && <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: colors.battery }} />Carga de batería</span>}
        <span className="eco-legend__item"><span className="eco-legend__dot" style={{ background: colors.export }} />Excedentes a red</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label="Consumo mensual y producción solar apilada">
        {yTicks(maxY).map((tick) => (
          <g key={tick}>
            <line x1={M.left} x2={W - M.right} y1={y(tick)} y2={y(tick)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 7} y={y(tick) + 3} textAnchor="end" fontSize="10" fill={INK_SOFT}>{Math.round(tick).toLocaleString('es-ES')}</text>
          </g>
        ))}
        {FLOW_MONTHS.map((month, i) => {
          const center = M.left + groupWidth * (i + 0.5)
          const consumption = flow.consumption[i] || 0
          const direct = flow.direct_self_consumption[i] || 0
          const charge = flow.battery_charge[i] || 0
          const exportEnergy = flow.grid_export[i] || 0
          const discharge = flow.battery_discharge[i] || 0
          let stacked = 0
          const segments = [
            { key: 'direct', label: 'Autoconsumo directo', value: direct, color: colors.direct },
            ...(flow.has_battery ? [{ key: 'charge', label: 'Carga de batería', value: charge, color: colors.battery }] : []),
            { key: 'export', label: 'Excedentes a red', value: exportEnergy, color: colors.export },
          ]
          return (
            <g key={month}>
              <title>{`${month}: consumo ${consumption.toLocaleString('es-ES', { maximumFractionDigits: 1 })} kWh; producción FV ${productionTotal[i].toLocaleString('es-ES', { maximumFractionDigits: 1 })} kWh; descarga de batería ${discharge.toLocaleString('es-ES', { maximumFractionDigits: 1 })} kWh`}</title>
              <rect x={center - barWidth - 1} y={y(consumption)} width={barWidth} height={Math.max(0, baseline - y(consumption))} fill={colors.consumption} />
              {segments.map((segment) => {
                const segmentTop = stacked + segment.value
                const rect = (
                  <rect key={segment.key} x={center + 1} y={y(segmentTop)} width={barWidth}
                    height={Math.max(0, y(stacked) - y(segmentTop))} fill={segment.color}>
                    <title>{`${month} · ${segment.label}: ${segment.value.toLocaleString('es-ES', { maximumFractionDigits: 1 })} kWh`}</title>
                  </rect>
                )
                stacked = segmentTop
                return rect
              })}
              <text x={center} y={H - M.bottom + 16} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{month}</text>
            </g>
          )
        })}
        <text x="14" y={(M.top + baseline) / 2} textAnchor="middle" fontSize="10" fill={INK} transform={`rotate(-90 14 ${(M.top + baseline) / 2})`}>kWh / mes</text>
      </svg>
      {flow.has_battery && <p className="eco-panel__note">La pila muestra energía FV destinada a consumo directo, carga de batería y excedentes. La descarga mensual puede incluir energía almacenada en meses anteriores; consúltala en el detalle de cada mes.</p>}
    </div>
  )
}

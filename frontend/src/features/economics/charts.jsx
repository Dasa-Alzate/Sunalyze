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

export function ProfitChart({ sweep }) {
  const series = sweep.series.filter((s) => s.costes)
  if (!series.length) {
    return (
      <p className="eco-panel__note">
        No hay precios completos para estimar la inversión: pon <strong>precio unitario</strong> al panel
        {sweep.sin_precio.length > 0 && <> y a {sweep.sin_precio.join(', ')}</>} en la biblioteca de equipos.
      </p>
    )
  }
  const W = 580
  const H = 300
  const M = { top: 16, right: 40, bottom: 36, left: 56 }
  const maxX = Math.max(...series.flatMap((s) => s.costes)) * 1.08
  const maxY = Math.max(...series.flatMap((s) => s.ahorros)) * 1.15
  const x = (v) => M.left + (v / maxX) * (W - M.left - M.right)
  const y = (v) => H - M.bottom - (v / maxY) * (H - M.top - M.bottom)
  const colorOf = (s) => SERIES_COLORS[sweep.series.indexOf(s)]

  return (
    <div>
      <Legend items={sweep.series.map((s) => s.nombre)} />
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label="Ahorro anual frente a inversión inicial, por batería">
        {yTicks(maxY).map((t) => (
          <g key={t}>
            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke={GRID} strokeWidth="1" />
            <text x={M.left - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill={INK_SOFT}>{eur0(t)}</text>
          </g>
        ))}
        {yTicks(maxX).map((t) => (
          <text key={t} x={x(t)} y={H - M.bottom + 16} textAnchor="middle" fontSize="10" fill={INK_SOFT}>{eur0(t)}</text>
        ))}
        {[3, 5, 8].map((anios) => {
          const yEdge = maxX / anios
          const clippedY = Math.min(yEdge, maxY)
          const xEnd = clippedY * anios
          return (
            <g key={anios}>
              <line x1={x(0)} y1={y(0)} x2={x(xEnd)} y2={y(clippedY)} stroke={GRID} strokeWidth="1" strokeDasharray="3 4" />
              <text x={x(xEnd) - 4} y={y(clippedY) + 12} textAnchor="end" fontSize="9" fill={INK_SOFT}>{anios} años</text>
            </g>
          )
        })}
        <text x={(M.left + W - M.right) / 2} y={H - 4} textAnchor="middle" fontSize="10" fill={INK}>Inversión inicial estimada (€, equipos + mano de obra)</text>
        {series.map((s) => (
          <g key={s.nombre}>
            <polyline
              points={s.costes.map((c, i) => `${x(c)},${y(s.ahorros[i])}`).join(' ')}
              fill="none" stroke={colorOf(s)} strokeWidth="2" strokeLinejoin="round"
            />
            {s.costes.map((c, i) => (
              <circle key={i} cx={x(c)} cy={y(s.ahorros[i])} r="4" fill={colorOf(s)} stroke="var(--surface-card)" strokeWidth="2">
                <title>{`${s.nombre} · ${sweep.kwp[i]} kWp · inversión ${eur0(c)} → ${eur0(s.ahorros[i])}/año (payback ${(c / s.ahorros[i]).toFixed(1)} años)`}</title>
              </circle>
            ))}
            {[0, s.costes.length - 1].map((i) => (
              <text key={i} x={x(s.costes[i])} y={y(s.ahorros[i]) - 8} textAnchor="middle" fontSize="9" fill={INK}>
                {sweep.kwp[i]} kWp
              </text>
            ))}
          </g>
        ))}
      </svg>
      {sweep.sin_precio.length > 0 && (
        <p className="eco-panel__note">Fuera de la gráfica por falta de precio: {sweep.sin_precio.join(', ')}.</p>
      )}
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
      <svg viewBox={`0 0 ${W} ${H}`} className="eco-chart" role="img" aria-label={`Consumo y producción de un día tipo de ${title.toLowerCase()}`}>
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
        <DayPanel title="Invierno" data={diaTipo.invierno} maxY={maxY} />
        <DayPanel title="Verano" data={diaTipo.verano} maxY={maxY} />
      </div>
      <p className="eco-panel__note">El hueco entre la curva azul y la mancha ámbar es lo que la batería puede desplazar.</p>
    </div>
  )
}

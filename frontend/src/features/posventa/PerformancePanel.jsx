import { useId, useState } from 'react'
import { Btn, Metric, Icon } from '@/shared/ui'
import { num, int, pct } from '@/shared/format'
import ReadingDialog from './ReadingDialog'

const GAUGE_MAX = 1.2

function polar(cx, cy, r, fraction) {
  const angle = Math.PI * (1 - fraction)
  return { x: cx + r * Math.cos(angle), y: cy - r * Math.sin(angle) }
}

function arcPath(cx, cy, r, fraction) {
  const start = polar(cx, cy, r, 0)
  const end = polar(cx, cy, r, fraction)
  const large = fraction > 0.5 ? 1 : 0
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`
}

function ratioTone(ratio) {
  if (ratio === null || ratio === undefined) return 'var(--text-muted)'
  if (ratio >= 0.9) return 'var(--state-valid)'
  if (ratio >= 0.7) return 'var(--state-warn)'
  return 'var(--danger)'
}

function PerformanceGauge({ ratio }) {
  const titleId = useId()
  const descId = useId()
  const cx = 100
  const cy = 95
  const r = 80
  const has = ratio !== null && ratio !== undefined
  const fraction = has ? Math.min(ratio, GAUGE_MAX) / GAUGE_MAX : 0
  const value = polar(cx, cy, r, fraction)
  const color = ratioTone(ratio)
  const label = has
    ? `Rendimiento real frente al esperado: ${pct(ratio)} por ciento.`
    : 'Sin baseline esperado para calcular el rendimiento.'

  return (
    <svg
      viewBox="0 0 200 120"
      width="100%"
      role="img"
      aria-labelledby={`${titleId} ${descId}`}
      style={{ display: 'block', maxWidth: 280, margin: '0 auto' }}
    >
      <title id={titleId}>Rendimiento real vs esperado</title>
      <desc id={descId}>{label}</desc>
      <path d={arcPath(cx, cy, r, 1)} fill="none" stroke="var(--border-strong)" strokeWidth="12" strokeLinecap="round" />
      {has && fraction > 0 && (
        <path d={arcPath(cx, cy, r, fraction)} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" />
      )}
      {has && <line x1={cx} y1={cy} x2={value.x} y2={value.y} stroke={color} strokeWidth="2.5" />}
      <circle cx={cx} cy={cy} r="4" fill={color} />
      <text x={cx} y={cy - 18} textAnchor="middle" fontSize="22" fontWeight="700" fill={color}>
        {has ? `${pct(ratio, 0)}%` : '—'}
      </text>
    </svg>
  )
}

export default function PerformancePanel({ performance, onAddReading }) {
  const [dialog, setDialog] = useState(false)
  const p = performance || {}

  return (
    <section aria-label="Rendimiento">
      <div className="sun-section-title">
        <Icon name="gauge" size={15} />Rendimiento esperado vs real
        <Btn variant="primary" size="sm" icon="plus" onClick={() => setDialog(true)} style={{ marginLeft: 'auto' }}>
          Añadir lectura
        </Btn>
      </div>

      <div className="posventa-performance">
        <PerformanceGauge ratio={p.ratio} />
        <div className="posventa-performance__metrics">
          <Metric label="Esperado anual" value={int(p.expected_annual_kwh)} unit="kWh" />
          <Metric label="Real acumulado" value={num(p.actual_total_kwh, 0)} unit="kWh" />
          <Metric label="Ratio real/esperado" value={p.ratio !== null && p.ratio !== undefined ? pct(p.ratio) : '—'} unit="%" />
          <Metric label="Lecturas" value={int(p.reading_count)} />
        </div>
      </div>

      <p className="posventa-note" role="note">
        <Icon name="info" size={14} />
        <span>Cifra indicativa. {p.method_note || 'Basada en lecturas manuales; el real fiable requiere monitorización automática (datalogger / API del inversor), pendiente.'}</span>
      </p>

      {dialog && (
        <ReadingDialog
          onClose={() => setDialog(false)}
          onSubmit={async (body) => { await onAddReading(body); setDialog(false) }}
        />
      )}
    </section>
  )
}

import { Icon, Badge } from '@/shared/ui'
import { num } from '@/shared/format'
import { INCENTIVE_KIND_LABELS } from './constants'

export default function IncentivesBreakdown({ incentives }) {
  const items = (incentives && incentives.items) || []
  const total = incentives?.total_eur || 0

  if (!items.length) {
    return null
  }

  return (
    <div className="finance-incentives">
      <div className="sun-section-title">
        <Icon name="badge-percent" size={15} />
        Desglose de incentivos
      </div>
      <div
        className="sun-card sun-card--flat"
        role="note"
        style={{ background: 'var(--warning-soft)', color: 'var(--warning-fg)', padding: 'var(--space-3)', marginBottom: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)' }}
      >
        <Icon name="alert-triangle" size={16} />
        <span style={{ fontSize: 'var(--text-sm)' }}>
          Mejor caso indicativo. El total suma todas las ayudas aplicables sin modelar
          incompatibilidades, topes combinados ni requisitos administrativos reales. Verifica cada
          subvención antes de comprometerla con el cliente.
        </span>
      </div>
      <table className="sun-table">
        <thead>
          <tr>
            <th scope="col">Incentivo</th>
            <th scope="col">Tipo</th>
            <th scope="col">Importe (€)</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it, i) => (
            <tr key={`${it.label || it.kind}-${i}`}>
              <td>{it.label || 'Incentivo'}</td>
              <td><Badge tone="neutral">{INCENTIVE_KIND_LABELS[it.kind] || it.kind}</Badge></td>
              <td>{num(it.amount, 0)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" colSpan={2}>Total (mejor caso)</th>
            <td><strong>{num(total, 0)}</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}

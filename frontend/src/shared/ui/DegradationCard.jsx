import { useState } from 'react'
import { Icon } from '@/shared/ui'
import { useTransition } from '@/services/transition'

export default function DegradationCard({ missing = [], assumptions = [] }) {
  const { navigate } = useTransition()
  const [open, setOpen] = useState(true)
  if (!missing.length && !assumptions.length) return null

  const byEquipment = new Map()
  for (const m of missing) {
    const key = `${m.entity}:${m.entity_id}`
    if (!byEquipment.has(key)) byEquipment.set(key, { nombre: m.entity_nombre, items: [], edit_url: m.edit_url })
    byEquipment.get(key).items.push(m)
  }

  return (
    <aside className="sun-degradation" role="note" aria-label="Cálculo con detalle reducido">
      <button type="button" className="sun-degradation__head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <Icon name="info" size={15} />
        <strong>Cálculo con detalle reducido</strong>
        <span className="sun-degradation__count">
          {missing.length > 0 && `${missing.length} dato${missing.length === 1 ? '' : 's'} pendiente${missing.length === 1 ? '' : 's'}`}
        </span>
        <Icon name={open ? 'chevron-up' : 'chevron-down'} size={14} />
      </button>
      {open && (
        <div className="sun-degradation__body">
          {[...byEquipment.values()].map((group) => (
            <div key={group.edit_url} className="sun-degradation__group">
              {group.nombre && <p className="sun-degradation__equipo">{group.nombre}</p>}
              <ul>
                {group.items.map((m) => (
                  <li key={m.field}>
                    <strong>{m.label}.</strong> Con este dato podríamos calcular: {m.unlocks}.
                  </li>
                ))}
              </ul>
              <a
                href={group.edit_url}
                onClick={(e) => { e.preventDefault(); navigate(group.edit_url) }}
              >
                Añadir el dato →
              </a>
            </div>
          ))}
          {assumptions.length > 0 && (
            <div className="sun-degradation__group sun-degradation__group--assumed">
              <p className="sun-degradation__equipo">Valores supuestos en este cálculo</p>
              <ul>
                {assumptions.map((a) => (
                  <li key={`${a.entity || ''}-${a.field}`}>
                    <strong>{a.label}{a.used != null ? ` = ${a.used}` : ''}.</strong> {a.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </aside>
  )
}

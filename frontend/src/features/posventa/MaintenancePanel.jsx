import { useState } from 'react'
import { Btn, Badge, IconBtn, Icon } from '@/shared/ui'
import { meta, VISIT_KIND, VISIT_STATUS, today } from './constants'
import VisitDialog from './VisitDialog'

export default function MaintenancePanel({ visits, onCreate, onUpdate, onDelete }) {
  const [dialog, setDialog] = useState(false)

  return (
    <section aria-label="Mantenimiento">
      <div className="sun-section-title">
        <Icon name="wrench" size={15} />Visitas de mantenimiento
        <Btn variant="primary" size="sm" icon="calendar-plus" onClick={() => setDialog(true)} style={{ marginLeft: 'auto' }}>
          Programar visita
        </Btn>
      </div>

      {visits.length === 0 ? (
        <p style={{ color: 'var(--text-subtle)' }}>No hay visitas registradas.</p>
      ) : (
        <ul className="posventa-list">
          {visits.map((v) => {
            const k = meta(VISIT_KIND, v.kind)
            const s = meta(VISIT_STATUS, v.status)
            return (
              <li key={v.id} className="posventa-item">
                <div className="posventa-item__main">
                  <span className="posventa-item__title">
                    <Badge tone={k.tone}>{k.label}</Badge>
                    <Badge tone={s.tone} icon={s.icon}>{s.label}</Badge>
                  </span>
                  <span className="posventa-item__meta">
                    {v.scheduled_at && <span><Icon name="calendar" size={13} /> {v.scheduled_at}</span>}
                    {v.done_at && <span><Icon name="check" size={13} /> {v.done_at}</span>}
                    {v.technician && <span><Icon name="user" size={13} /> {v.technician}</span>}
                  </span>
                  {v.notes && <p className="posventa-item__notes">{v.notes}</p>}
                </div>
                <span className="posventa-item__actions">
                  {v.status === 'programada' && (
                    <Btn
                      variant="secondary"
                      size="sm"
                      icon="check"
                      onClick={() => onUpdate(v.id, { status: 'realizada', done_at: today() })}
                    >
                      Marcar realizada
                    </Btn>
                  )}
                  <IconBtn icon="trash-2" label={`Eliminar visita ${k.label}`} size="sm" onClick={() => onDelete(v.id)} />
                </span>
              </li>
            )
          })}
        </ul>
      )}

      {dialog && (
        <VisitDialog
          onClose={() => setDialog(false)}
          onSubmit={async (body) => { await onCreate(body); setDialog(false) }}
        />
      )}
    </section>
  )
}

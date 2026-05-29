import { useState } from 'react'
import { Btn, Badge, IconBtn, Icon } from '@/shared/ui'
import { meta, INCIDENT_SEVERITY, INCIDENT_STATUS, today } from './constants'
import IncidentDialog from './IncidentDialog'

export default function IncidentsPanel({ incidents, onCreate, onUpdate, onDelete }) {
  const [dialog, setDialog] = useState(false)

  return (
    <section aria-label="Incidencias">
      <div className="sun-section-title">
        <Icon name="alert-triangle" size={15} />Incidencias
        <Btn variant="primary" size="sm" icon="plus" onClick={() => setDialog(true)} style={{ marginLeft: 'auto' }}>
          Abrir incidencia
        </Btn>
      </div>

      {incidents.length === 0 ? (
        <p style={{ color: 'var(--text-subtle)' }}>No hay incidencias registradas.</p>
      ) : (
        <ul className="posventa-list">
          {incidents.map((i) => {
            const sev = meta(INCIDENT_SEVERITY, i.severity)
            const st = meta(INCIDENT_STATUS, i.status)
            return (
              <li key={i.id} className="posventa-item">
                <div className="posventa-item__main">
                  <span className="posventa-item__title">
                    <strong>{i.title}</strong>
                    <Badge tone={sev.tone}>{sev.label}</Badge>
                    <Badge tone={st.tone} icon={st.icon}>{st.label}</Badge>
                  </span>
                  <span className="posventa-item__meta">
                    {i.opened_at && <span><Icon name="calendar" size={13} /> Abierta {i.opened_at}</span>}
                    {i.resolved_at && <span><Icon name="check" size={13} /> Resuelta {i.resolved_at}</span>}
                  </span>
                  {i.description && <p className="posventa-item__notes">{i.description}</p>}
                </div>
                <span className="posventa-item__actions">
                  {i.status !== 'resuelta' && (
                    <Btn
                      variant="secondary"
                      size="sm"
                      icon="circle-check"
                      onClick={() => onUpdate(i.id, { status: 'resuelta', resolved_at: today() })}
                    >
                      Resolver
                    </Btn>
                  )}
                  <IconBtn icon="trash-2" label={`Eliminar incidencia ${i.title}`} size="sm" onClick={() => onDelete(i.id)} />
                </span>
              </li>
            )
          })}
        </ul>
      )}

      {dialog && (
        <IncidentDialog
          onClose={() => setDialog(false)}
          onSubmit={async (body) => { await onCreate(body); setDialog(false) }}
        />
      )}
    </section>
  )
}

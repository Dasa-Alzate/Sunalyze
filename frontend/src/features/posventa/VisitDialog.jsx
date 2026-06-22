import { useState } from 'react'
import { Scrim, Field, SelectField, Btn } from '@/shared/ui'
import { today } from './constants'

export default function VisitDialog({ onClose, onSubmit }) {
  const [kind, setKind] = useState('preventivo')
  const [scheduledAt, setScheduledAt] = useState(today())
  const [technician, setTechnician] = useState('')
  const [notes, setNotes] = useState('')

  async function submit() {
    await onSubmit({
      kind,
      status: 'programada',
      scheduled_at: scheduledAt || null,
      technician: technician.trim() || null,
      notes: notes.trim() || null,
    })
  }

  return (
    <Scrim label="Programar visita de mantenimiento" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Programar visita</h3></header>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <SelectField
              label="Tipo de visita"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              options={[{ value: 'preventivo', label: 'Preventivo' }, { value: 'correctivo', label: 'Correctivo' }]}
            />
            <Field label="Fecha programada" type="date" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
            <Field label="Técnico" placeholder="Nombre del técnico" value={technician} onChange={(e) => setTechnician(e.target.value)} />
            <Field label="Notas" placeholder="Detalles de la visita" value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="calendar-plus" onClick={submit}>Programar</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

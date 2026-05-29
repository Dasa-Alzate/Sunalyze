import { useState } from 'react'
import { Scrim, Field, SelectField, Btn } from '@/shared/ui'
import { INCIDENT_SEVERITY, today } from './constants'

const SEVERITY_OPTIONS = Object.keys(INCIDENT_SEVERITY).map((value) => ({
  value,
  label: INCIDENT_SEVERITY[value].label,
}))

export default function IncidentDialog({ onClose, onSubmit }) {
  const [title, setTitle] = useState('')
  const [severity, setSeverity] = useState('media')
  const [description, setDescription] = useState('')
  const [error, setError] = useState(null)

  async function submit() {
    if (!title.trim()) {
      setError('Indica un título para la incidencia.')
      return
    }
    await onSubmit({
      title: title.trim(),
      severity,
      status: 'abierta',
      opened_at: today(),
      description: description.trim() || null,
    })
  }

  return (
    <Scrim label="Abrir incidencia" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Abrir incidencia</h3></header>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <Field
              label="Título"
              required
              placeholder="Inversor sin comunicación"
              value={title}
              error={error}
              onChange={(e) => { setTitle(e.target.value); setError(null) }}
            />
            <SelectField
              label="Severidad"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              options={SEVERITY_OPTIONS}
            />
            <Field label="Descripción" placeholder="Detalle de la incidencia" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="plus" onClick={submit}>Abrir incidencia</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

import { useState } from 'react'
import { Scrim, Field, Btn } from '@/shared/ui'

export default function ReadingDialog({ onClose, onSubmit }) {
  const [period, setPeriod] = useState('')
  const [actualKwh, setActualKwh] = useState('')
  const [error, setError] = useState(null)

  async function submit() {
    if (!period.trim()) {
      setError('Indica el periodo de la lectura.')
      return
    }
    if (actualKwh === '' || Number.isNaN(Number(actualKwh))) {
      setError('Indica los kWh leídos.')
      return
    }
    await onSubmit({ period: period.trim(), actual_kwh: Number(actualKwh) })
  }

  return (
    <Scrim label="Añadir lectura de producción" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Añadir lectura</h3></header>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <Field
              label="Periodo"
              required
              placeholder="2026-05"
              hint="Mes (AAAA-MM) o etiqueta del periodo medido."
              value={period}
              onChange={(e) => { setPeriod(e.target.value); setError(null) }}
            />
            <Field
              label="Producción real (kWh)"
              required
              type="number"
              numeric
              placeholder="720"
              value={actualKwh}
              error={error}
              onChange={(e) => { setActualKwh(e.target.value); setError(null) }}
            />
          </div>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="plus" onClick={submit}>Guardar lectura</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

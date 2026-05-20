import { useState } from 'react'
import { Scrim, Btn, Field, SelectField } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { DOCUMENT_KINDS } from './constants'

export default function CreateTemplateDialog({ onCreated, onClose }) {
  const [name, setName] = useState('')
  const [kind, setKind] = useState(DOCUMENT_KINDS[0].value)
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    if (!name.trim()) { toast('warning', 'El nombre es obligatorio'); return }
    setBusy(true)
    try {
      const tpl = await api.templates.create({ name: name.trim(), kind, description: description.trim() })
      toast('success', 'Plantilla creada')
      onCreated(tpl)
    } catch (e) {
      toast('error', 'No se pudo crear', e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Scrim label="Nueva plantilla" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Nueva plantilla</h3></header>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <Field label="Nombre" required value={name} onChange={(e) => setName(e.target.value)} />
            <SelectField label="Tipo de documento" value={kind} onChange={(e) => setKind(e.target.value)} options={DOCUMENT_KINDS} />
            <Field label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="plus" busy={busy} onClick={submit}>Crear</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

import { useState } from 'react'
import { Btn, Field, Icon, Scrim } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

export function ImportProfileModal({ onClose, onImported }) {
  const [file, setFile] = useState(null)
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (!file) { setError('Elige un archivo CSV o JSON.'); return }
    setBusy(true)
    setError(null)
    try {
      const profile = await api.consumptionProfiles.importFile(file, name.trim() || undefined)
      toast('success', 'Perfil importado', `«${profile.name}» ya está disponible para tus proyectos.`)
      onImported(profile)
    } catch (err) {
      setError(err.data?.error || err.message)
      setBusy(false)
    }
  }

  return (
    <Scrim onClose={onClose} label="Importar perfil de consumo" center>
      <div className="cp-import">
        <h3><Icon name="upload" size={16} /> Importar perfil de consumo</h3>
        <p className="cp-import__hint">
          Curva horaria o cuartohoraria del contador (CSV de Datadis o de la distribuidora), de un año
          completo o de un mes natural. También se admite un JSON de 8.760 valores.
        </p>
        <form onSubmit={submit}>
          <Field label="Archivo" required>
            <input
              type="file"
              className="sun-input"
              accept=".csv,.json"
              onChange={(e) => { setFile(e.target.files[0] || null); setError(null) }}
            />
          </Field>
          <Field label="Nombre del perfil" hint="Si lo dejas vacío, se usa el nombre del archivo"
            value={name} onChange={(e) => setName(e.target.value)} placeholder="Consumo — Panadería Martínez" />
          {error && (
            <p className="cp-import__error"><Icon name="alert-triangle" size={13} /> {error}</p>
          )}
          <div className="cp-import__actions">
            <Btn variant="ghost" onClick={onClose} type="button">Cancelar</Btn>
            <Btn variant="primary" icon="upload" type="submit" disabled={busy} data-busy={busy}>
              {busy ? 'Importando…' : 'Importar'}
            </Btn>
          </div>
        </form>
      </div>
    </Scrim>
  )
}

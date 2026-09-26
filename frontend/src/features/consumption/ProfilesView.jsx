import { useEffect, useState } from 'react'
import { Badge, Btn, ConfirmDialog, Field, Icon, IconBtn, Scrim, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { ImportProfileModal } from './ImportProfileModal'
import { KIND_LABELS, originBadge } from './ConsumptionProfileSection'
import './consumption.css'

export function ProfilesView({ canEdit }) {
  const [profiles, setProfiles] = useState(null)
  const [importing, setImporting] = useState(false)
  const [renaming, setRenaming] = useState(null)
  const [newName, setNewName] = useState('')
  const [deleting, setDeleting] = useState(null)

  async function load() {
    try {
      setProfiles(await api.consumptionProfiles.list())
    } catch (err) {
      toast('error', 'No se pudieron cargar los perfiles', err.message)
      setProfiles([])
    }
  }

  useEffect(() => { load() }, [])

  async function rename(e) {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    try {
      await api.consumptionProfiles.update(renaming.id, { name })
      toast('success', 'Perfil renombrado')
      setRenaming(null)
      load()
    } catch (err) {
      toast('error', 'No se pudo renombrar', err.data?.error || err.message)
    }
  }

  async function remove() {
    try {
      await api.consumptionProfiles.remove(deleting.id)
      toast('success', 'Perfil eliminado', `«${deleting.name}» ya no está disponible para proyectos nuevos.`)
      setDeleting(null)
      load()
    } catch (err) {
      toast('error', 'No se pudo eliminar', err.data?.error || err.message)
    }
  }

  if (profiles === null) return <Spinner label="Cargando perfiles…" />

  return (
    <>
      <div className="cp-library__bar">
        {canEdit && <Btn variant="primary" icon="upload" onClick={() => setImporting(true)}>Subir CSV</Btn>}
      </div>
      <table className="sun-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Tipo</th>
            <th>Origen</th>
            <th style={{ textAlign: 'right' }}>Muestra (kWh/año)</th>
            <th aria-label="Acciones" />
          </tr>
        </thead>
        <tbody>
          {profiles.map((p) => (
            <tr key={p.id}>
              <td className="cp-table-name">{p.name}</td>
              <td>{KIND_LABELS[p.kind] || p.kind}</td>
              <td><Badge tone={originBadge(p).tone}>{originBadge(p).label}</Badge></td>
              <td style={{ textAlign: 'right' }}>
                {p.annual_kwh_hint != null ? Math.round(p.annual_kwh_hint).toLocaleString('es-ES') : '—'}
              </td>
              <td style={{ textAlign: 'right' }}>
                {canEdit && !p.is_global && (
                  <>
                    <IconBtn icon="pencil" label={`Renombrar ${p.name}`} size="sm"
                      onClick={() => { setRenaming(p); setNewName(p.name) }} />
                    <IconBtn icon="trash-2" label={`Eliminar ${p.name}`} size="sm"
                      onClick={() => setDeleting(p)} />
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {importing && (
        <ImportProfileModal
          onClose={() => setImporting(false)}
          onImported={() => { setImporting(false); load() }}
        />
      )}
      {renaming && (
        <Scrim onClose={() => setRenaming(null)} label="Renombrar perfil" center>
          <div className="cp-import">
            <h3><Icon name="pencil" size={16} /> Renombrar perfil</h3>
            <form onSubmit={rename}>
              <Field label="Nombre" required value={newName} onChange={(e) => setNewName(e.target.value)} />
              <div className="cp-import__actions">
                <Btn variant="ghost" type="button" onClick={() => setRenaming(null)}>Cancelar</Btn>
                <Btn variant="primary" icon="save" type="submit">Guardar</Btn>
              </div>
            </form>
          </div>
        </Scrim>
      )}
      <ConfirmDialog
        open={Boolean(deleting)}
        title="Eliminar perfil de consumo"
        description={deleting ? `«${deleting.name}» dejará de estar disponible; los proyectos que ya lo usan no se tocan.` : ''}
        onClose={() => setDeleting(null)}
        actions={[
          { label: 'Cancelar', variant: 'ghost', onClick: () => setDeleting(null) },
          { label: 'Eliminar', variant: 'danger', icon: 'trash-2', onClick: remove },
        ]}
      />
    </>
  )
}

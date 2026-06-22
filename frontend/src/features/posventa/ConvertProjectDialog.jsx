import { useEffect, useState } from 'react'
import { Scrim, SelectField, Btn, Spinner, Icon } from '@/shared/ui'
import { api } from '@/api/client'

export default function ConvertProjectDialog({ existingProjectIds, onClose, onSubmit }) {
  const [projects, setProjects] = useState(null)
  const [projectId, setProjectId] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    api.projects.list('aprobado')
      .then((list) => {
        if (!alive) return
        const available = (list || []).filter((p) => !existingProjectIds.includes(p.id))
        setProjects(available)
        setProjectId(available[0] ? String(available[0].id) : '')
      })
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [existingProjectIds])

  async function submit() {
    if (!projectId) return
    await onSubmit(Number(projectId))
  }

  return (
    <Scrim label="Convertir proyecto en instalación" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Convertir en instalación</h3></header>
        <div className="sun-drawer__body">
          {projects === null ? (
            <Spinner label="Cargando proyectos aprobados…" />
          ) : error ? (
            <p className="sun-field__error"><Icon name="alert-circle" size={13} />{error}</p>
          ) : projects.length === 0 ? (
            <p style={{ color: 'var(--text-subtle)' }}>
              No hay proyectos aprobados sin instalación. Aprueba un proyecto para poder ponerlo en marcha.
            </p>
          ) : (
            <div className="sun-speclist">
              <SelectField
                label="Proyecto aprobado"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                options={projects.map((p) => ({ value: String(p.id), label: p.cliente || `Proyecto ${p.id}` }))}
              />
            </div>
          )}
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="plug-zap" disabled={!projectId} onClick={submit}>Crear instalación</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

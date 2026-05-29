import { useEffect, useState } from 'react'
import { Topbar, Card, Btn, Badge, Spinner, ErrorState, Icon } from '@/shared/ui'
import { api, ApiError } from '@/api/client'
import { toast } from '@/services/toast'
import { meta, INSTALLATION_STATUS } from './constants'
import InstallationDetail from './InstallationDetail'
import ConvertProjectDialog from './ConvertProjectDialog'

function InstallationCard({ installation, onOpen }) {
  const s = meta(INSTALLATION_STATUS, installation.status)
  return (
    <Card className="sun-card--pad posventa-card">
      <button type="button" className="posventa-card__btn" onClick={() => onOpen(installation.id)}>
        <span className="posventa-card__head">
          <strong>{installation.cliente || `Instalación ${installation.id}`}</strong>
          <Badge tone={s.tone} icon={s.icon}>{s.label}</Badge>
        </span>
        <span className="posventa-card__meta">
          <span><Icon name="shield-check" size={13} /> Garantía {installation.warranty_until || '—'}</span>
          <span><Icon name="wrench" size={13} /> {installation.maintenance_count} visitas</span>
          <span><Icon name="alert-triangle" size={13} /> {installation.incident_count} incidencias</span>
        </span>
      </button>
    </Card>
  )
}

export default function InstallationsWorkspace() {
  const [installations, setInstallations] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [convert, setConvert] = useState(false)

  function load() {
    setError(null)
    return api.installations.list()
      .then((list) => setInstallations(list || []))
      .catch((e) => setError(e instanceof ApiError ? e.message : 'No se pudieron cargar las instalaciones.'))
  }

  useEffect(() => {
    let alive = true
    api.installations.list()
      .then((list) => alive && setInstallations(list || []))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : 'No se pudieron cargar las instalaciones.'))
    return () => { alive = false }
  }, [])

  async function createFromProject(projectId) {
    try {
      const created = await api.installations.create(projectId)
      toast('success', 'Instalación creada')
      setConvert(false)
      await load()
      setSelected(created.id)
    } catch (e) {
      toast('error', 'No se pudo crear la instalación', e.message)
    }
  }

  if (selected) {
    return (
      <InstallationDetail
        installationId={selected}
        onBack={() => { setSelected(null); load() }}
      />
    )
  }

  return (
    <>
      <Topbar
        title="Instalaciones"
        crumb="Posventa"
        actions={<Btn variant="primary" icon="plug-zap" onClick={() => setConvert(true)}>Convertir en instalación</Btn>}
      />

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : installations === null ? (
        <Spinner label="Cargando instalaciones…" />
      ) : installations.length === 0 ? (
        <Card className="sun-card--pad">
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="plug-zap" size={26} /></div>
            <div className="sun-empty__title">Aún no hay instalaciones</div>
            <div className="sun-empty__desc">Convierte un proyecto aprobado en una instalación para empezar el seguimiento de posventa.</div>
            <div className="sun-empty__actions">
              <Btn variant="primary" icon="plug-zap" onClick={() => setConvert(true)}>Convertir en instalación</Btn>
            </div>
          </div>
        </Card>
      ) : (
        <div className="posventa-grid">
          {installations.map((i) => (
            <InstallationCard key={i.id} installation={i} onOpen={setSelected} />
          ))}
        </div>
      )}

      {convert && (
        <ConvertProjectDialog
          existingProjectIds={(installations || []).map((i) => i.project_id)}
          onClose={() => setConvert(false)}
          onSubmit={createFromProject}
        />
      )}
    </>
  )
}

import { useEffect, useState } from 'react'
import { Card, Badge, Btn, SelectField, Spinner, ErrorState, Icon } from '@/shared/ui'
import { api, ApiError } from '@/api/client'
import { toast } from '@/services/toast'
import { meta, INSTALLATION_STATUS, INSTALLATION_STATUS_OPTIONS } from './constants'
import MaintenancePanel from './MaintenancePanel'
import IncidentsPanel from './IncidentsPanel'
import PerformancePanel from './PerformancePanel'

const TABS = [
  { key: 'mantenimiento', label: 'Mantenimiento', icon: 'wrench' },
  { key: 'incidencias', label: 'Incidencias', icon: 'alert-triangle' },
  { key: 'rendimiento', label: 'Rendimiento', icon: 'gauge' },
]

export default function InstallationDetail({ installationId, onBack }) {
  const [tab, setTab] = useState('mantenimiento')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  function reload() {
    setError(null)
    return api.installations.get(installationId)
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'No se pudo cargar la instalación.'))
  }

  useEffect(() => {
    let alive = true
    api.installations.get(installationId)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : 'No se pudo cargar la instalación.'))
    return () => { alive = false }
  }, [installationId])

  async function changeStatus(status) {
    try {
      await api.installations.update(installationId, { status })
      toast('success', 'Estado actualizado')
      await reload()
    } catch (e) {
      toast('error', 'No se pudo cambiar el estado', e.message)
    }
  }

  async function run(promise, ok) {
    try {
      await promise
      if (ok) toast('success', ok)
      await reload()
    } catch (e) {
      toast('error', 'Operación fallida', e.message)
    }
  }

  if (error) return <div className="sun-content"><ErrorState message={error} onRetry={reload} /></div>
  if (!data) return <div className="sun-content"><Spinner label="Cargando instalación…" /></div>

  const s = meta(INSTALLATION_STATUS, data.status)

  return (
    <div className="sun-content">
      <div className="posventa-detail__head">
        <Btn variant="ghost" size="sm" icon="arrow-left" onClick={onBack}>Volver</Btn>
        <h2 className="posventa-detail__title">
          {data.cliente || `Instalación ${data.id}`}
          <Badge tone={s.tone} icon={s.icon}>{s.label}</Badge>
        </h2>
        <div className="posventa-detail__statuschange">
          <SelectField
            label="Estado"
            value={data.status}
            onChange={(e) => changeStatus(e.target.value)}
            options={INSTALLATION_STATUS_OPTIONS}
          />
        </div>
      </div>

      <Card className="sun-card--pad posventa-detail__summary">
        <span><Icon name="calendar-check" size={14} /> Puesta en marcha: {data.commissioned_at || '—'}</span>
        <span><Icon name="shield-check" size={14} /> Garantía: {data.warranty_until || '—'}</span>
        <span><Icon name="folder" size={14} /> Proyecto #{data.project_id}</span>
      </Card>

      <div className="sun-tabs" role="tablist" aria-label="Secciones de la instalación" style={{ marginBottom: 'var(--space-5)' }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            className={`sun-tab${tab === t.key ? ' sun-tab--active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            <Icon name={t.icon} size={16} />{t.label}
          </button>
        ))}
      </div>

      <Card className="sun-card--pad">
        {tab === 'mantenimiento' && (
          <MaintenancePanel
            visits={data.maintenance || []}
            onCreate={(b) => run(api.installations.maintenance.create(installationId, b), 'Visita programada')}
            onUpdate={(vid, b) => run(api.installations.maintenance.update(installationId, vid, b), 'Visita actualizada')}
            onDelete={(vid) => run(api.installations.maintenance.remove(installationId, vid), 'Visita eliminada')}
          />
        )}
        {tab === 'incidencias' && (
          <IncidentsPanel
            incidents={data.incidents || []}
            onCreate={(b) => run(api.installations.incidents.create(installationId, b), 'Incidencia abierta')}
            onUpdate={(iid, b) => run(api.installations.incidents.update(installationId, iid, b), 'Incidencia actualizada')}
            onDelete={(iid) => run(api.installations.incidents.remove(installationId, iid), 'Incidencia eliminada')}
          />
        )}
        {tab === 'rendimiento' && (
          <PerformancePanel
            performance={data.performance}
            onAddReading={(b) => run(api.installations.readings.create(installationId, b), 'Lectura añadida')}
          />
        )}
      </Card>
    </div>
  )
}

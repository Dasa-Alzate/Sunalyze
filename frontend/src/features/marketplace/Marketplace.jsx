import { useEffect, useState } from 'react'
import { Topbar } from '@/shared/ui'
import { Btn, Icon, Badge, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { useAuth } from '@/services/auth'
import { num } from '@/shared/format'

export default function Marketplace() {
  const { can } = useAuth()
  const canManage = can('module:manage')
  const [modules, setModules] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setModules(null)
    api.modules.list().then(setModules).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  async function toggle(m) {
    try {
      if (m.enabled) {
        await api.modules.disable(m.key)
        toast('info', 'Módulo desactivado', m.titulo)
      } else {
        await api.modules.enable(m.key)
        toast('success', 'Módulo activado', m.titulo)
      }
      load()
    } catch (e) {
      toast('error', 'No se pudo actualizar', e.message)
    }
  }

  const priceLabel = (p) => (p == null ? '' : p === 0 ? 'Incluido' : `${num(p)} €/mes`)

  return (
    <>
      <Topbar title="Módulos" crumb="Marketplace" />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : modules === null ? (
          <Spinner label="Cargando módulos…" />
        ) : modules.length === 0 ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="store" size={26} /></div>
            <div className="sun-empty__title">Sin módulos disponibles</div>
            <div className="sun-empty__desc">Aún no hay módulos publicados en el marketplace.</div>
          </div>
        ) : (
          <div className="catalog-grid">
            {modules.map((m) => (
              <div className="sun-card module-card" key={m.key}>
                <div className="module-card__media">
                  {m.thumbnail_path
                    ? <img src={m.thumbnail_path} alt={m.titulo} />
                    : <Icon name="package" size={28} color="var(--green-600)" />}
                </div>
                <div className="module-card__body">
                  <div className="module-card__head">
                    <strong className="module-card__title">{m.titulo || m.nombre}</strong>
                    {m.enabled
                      ? <Badge tone="success" icon="check">Activo</Badge>
                      : <span className="module-card__price">{priceLabel(m.price)}</span>}
                  </div>
                  <p className="module-card__desc">{m.descripcion}</p>
                  <div className="module-card__foot">
                    {canManage ? (
                      m.enabled
                        ? <Btn variant="secondary" size="sm" icon="check" onClick={() => toggle(m)}>Activado · Desactivar</Btn>
                        : <Btn variant="primary" size="sm" icon="plus" onClick={() => toggle(m)}>Activar</Btn>
                    ) : (
                      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-subtle)' }}>
                        {m.enabled ? 'Disponible en tu espacio' : 'Pídelo a un administrador'}
                      </span>
                    )}
                    {m.help_url && m.help_url !== '#' && (
                      <a href={m.help_url} target="_blank" rel="noreferrer" style={{ marginLeft: 'auto', fontSize: 'var(--text-sm)' }}>Ayuda</a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Topbar } from '@/shared/ui'
import { Btn, IconBtn, Badge, Dot, Icon, ExportMenu, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { estadoMeta, relativo } from '@/shared/estados'
import { dec } from '@/shared/format'
import { exportRows } from '@/services/export'
import { toast } from '@/services/toast'
import { useAuth } from '@/services/auth'

export default function ProjectList() {
  const nav = useNavigate()
  const { can } = useAuth()
  const [all, setAll] = useState(null)
  const [error, setError] = useState(null)
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('todos')

  function load() {
    setError(null)
    setAll(null)
    api.projects.list().then(setAll).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  const rows = (all || []).filter((p) => {
    const okq = (`${p.cliente} ${p.direccion || ''}`).toLowerCase().includes(q.toLowerCase())
    const oke = estado === 'todos' || p.estado === estado
    return okq && oke
  })

  async function duplicate(id) {
    try {
      await api.projects.duplicate(id)
      toast('success', 'Proyecto duplicado')
      load()
    } catch (e) {
      toast('error', 'No se pudo duplicar', e.message)
    }
  }

  async function remove(id, cliente) {
    if (!window.confirm(`¿Eliminar el proyecto de ${cliente}? Esta acción no se puede deshacer.`)) return
    try {
      await api.projects.remove(id)
      toast('success', 'Proyecto eliminado')
      load()
    } catch (e) {
      toast('error', 'No se pudo eliminar', e.message)
    }
  }

  return (
    <>
      <Topbar
        title="Proyectos"
        actions={<Btn variant="primary" icon="plus" onClick={() => nav('/app/diseno')}>Nuevo proyecto</Btn>}
      />
      <div className="sun-content">
        <div className="sun-toolbar">
          <div className="sun-toolbar__search">
            <div className="sun-input-group">
              <span className="sun-input-group__icon"><Icon name="search" size={16} /></span>
              <input className="sun-input" placeholder="Buscar cliente o dirección…" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
          </div>
          <select className="sun-select" style={{ width: 180 }} value={estado} onChange={(e) => setEstado(e.target.value)}>
            <option value="todos">Todos los estados</option>
            <option value="memoria">Memoria</option>
            <option value="diseno">Diseño</option>
            <option value="borrador">Borrador</option>
          </select>
          <div style={{ marginLeft: 'auto' }}>
            <ExportMenu
              label="Exportar"
              onExport={(fmt) => exportRows(fmt, 'proyectos', ['Cliente', 'Dirección', 'Panel', 'kWp', 'Estado', 'Modificado'],
                rows.map((p) => [p.cliente, p.direccion || '', p.panel_nombre || '', p.kwp ?? '', estadoMeta(p.estado).label, relativo(p.updated_at)]))}
            />
          </div>
        </div>

        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : !all ? (
          <Spinner label="Cargando proyectos…" />
        ) : rows.length === 0 ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="sun" size={26} /></div>
            <div className="sun-empty__title">{all.length === 0 ? 'Aún no hay proyectos' : 'Sin resultados'}</div>
            <div className="sun-empty__desc">
              {all.length === 0
                ? 'Crea tu primer proyecto: de coordenadas a memoria técnica firmable en 10 minutos.'
                : 'Ningún proyecto coincide con el filtro. Prueba a limpiar la búsqueda o crea uno nuevo.'}
            </div>
            <div className="sun-empty__actions">
              <Btn variant="primary" icon="plus" onClick={() => nav('/app/diseno')}>{all.length === 0 ? 'Crear tu primer proyecto' : 'Crear proyecto'}</Btn>
              {all.length > 0 && <Btn variant="secondary" onClick={() => { setQ(''); setEstado('todos') }}>Limpiar filtros</Btn>}
            </div>
          </div>
        ) : (
          <div className="sun-card" style={{ overflow: 'hidden' }}>
            <table className="sun-table">
              <thead>
                <tr>
                  <th>Cliente / Dirección</th>
                  <th>Panel</th>
                  <th style={{ textAlign: 'right' }}>kWp</th>
                  <th>Estado</th>
                  <th style={{ textAlign: 'right' }}>Modificado</th>
                  <th style={{ width: 96 }}></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => {
                  const e = estadoMeta(p.estado)
                  return (
                    <tr
                      key={p.id}
                      className="is-clickable"
                      role="button"
                      tabIndex={0}
                      aria-label={`Abrir diseño de ${p.cliente}`}
                      onClick={() => nav(`/app/diseno/${p.id}`)}
                      onKeyDown={(ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); nav(`/app/diseno/${p.id}`) } }}
                    >
                      <td>
                        <div className="sun-cell-client">
                          <strong style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                            {p.serial && <Badge tone="neutral"><span className="mono">{p.serial}</span></Badge>}
                            {p.cliente}
                          </strong>
                          <span>{p.direccion || '—'}</span>
                        </div>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>
                        {p.panel_nombre ? <>{p.panel_nombre}{p.n_paneles ? <> · <span className="num">{p.n_paneles}</span> ud</> : null}</> : '—'}
                      </td>
                      <td className="num" style={{ textAlign: 'right' }}>{p.kwp != null ? dec(p.kwp) : '—'}</td>
                      <td><span className="sun-cell-status"><Dot state={e.dot} /><Badge tone={e.tone}>{e.label}</Badge></span></td>
                      <td style={{ textAlign: 'right', color: 'var(--text-subtle)', fontSize: 'var(--text-xs)' }}>{relativo(p.updated_at)}</td>
                      <td onClick={(ev) => ev.stopPropagation()}>
                        <span style={{ display: 'inline-flex', gap: 4, justifyContent: 'flex-end', width: '100%' }}>
                          {can('project:create') && <IconBtn icon="copy" label="Duplicar" size="sm" onClick={() => duplicate(p.id)} />}
                          {can('project:delete') && <IconBtn icon="trash-2" label="Eliminar" size="sm" onClick={() => remove(p.id, p.cliente)} />}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}

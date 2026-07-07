import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Topbar } from '@/shared/ui'
import { Btn, Dot, Badge, Icon, Card, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { estadoMeta, relativo } from '@/shared/estados'
import { dec } from '@/shared/format'
import PendingWorkPanel from '@/features/notifications/PendingWorkPanel'

export default function Dashboard() {
  const nav = useNavigate()
  const [projects, setProjects] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setProjects(null)
    api.projects.list().then(setProjects).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  const kpis = buildKpis(projects)

  return (
    <>
      <Topbar
        title="Resumen"
        actions={<Btn variant="primary" icon="plus" onClick={() => nav('/app/diseno')}>Nuevo diseño</Btn>}
      />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : !projects ? (
          <Spinner label="Cargando proyectos…" />
        ) : projects.length === 0 ? (
          <WelcomeCard onCreate={() => nav('/app/diseno')} />
        ) : (
          <>
            <div className="sun-kpis">
              {kpis.map((k) => (
                <div className="sun-kpi" key={k.label}>
                  <div className="sun-kpi__top">
                    <span className="sun-metric__label">{k.label}</span>
                    <span className="sun-kpi__icon" style={{ background: k.bg, color: k.fg }}><Icon name={k.icon} size={18} /></span>
                  </div>
                  <span className="sun-metric__value">{k.value}{k.unit && <span className="unit">{k.unit}</span>}</span>
                </div>
              ))}
            </div>

            <div className="sun-grid-2">
              <Card>
                <div className="sun-card__header">
                  <span className="sun-card__title">Proyectos recientes</span>
                  <div style={{ marginLeft: 'auto' }}>
                    <Btn variant="ghost" size="sm" iconRight="arrow-right" onClick={() => nav('/app/proyectos')}>Ver todos</Btn>
                  </div>
                </div>
                {projects.length === 0 ? (
                  <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Aún no hay proyectos. Crea el primero con «Nuevo diseño».
                  </div>
                ) : (
                  <table className="sun-table">
                    <thead>
                      <tr><th>Cliente</th><th style={{ textAlign: 'right' }}>kWp</th><th>Estado</th><th style={{ textAlign: 'right' }}>Modificado</th></tr>
                    </thead>
                    <tbody>
                      {projects.slice(0, 5).map((p) => {
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
                            <td><div className="sun-cell-client"><strong>{p.cliente}</strong><span>{p.direccion || '—'}</span></div></td>
                            <td className="num" style={{ textAlign: 'right' }}>{p.kwp != null ? dec(p.kwp) : '—'}</td>
                            <td><span className="sun-cell-status"><Dot state={e.dot} /><Badge tone={e.tone}>{e.label}</Badge></span></td>
                            <td style={{ textAlign: 'right', color: 'var(--text-subtle)', fontSize: 'var(--text-xs)' }}>{relativo(p.updated_at)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </Card>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
                <PendingWorkPanel />
                <Card className="sun-card--pad">
                  <div className="sun-section-title"><h3>Empezar</h3></div>
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>De coordenadas a memoria técnica firmable en 10 minutos.</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                    <Btn variant="primary" icon="plus" block onClick={() => nav('/app/diseno')}>Nuevo diseño</Btn>
                    <Btn variant="secondary" icon="copy" block onClick={() => nav('/app/proyectos')}>Duplicar una plantilla</Btn>
                  </div>
                </Card>
                <Card className="sun-card--pad" style={{ background: 'var(--surface-brand-soft)', borderColor: 'var(--green-200)' }}>
                  <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                    <Icon name="sun" size={22} color="var(--green-600)" />
                    <div>
                      <strong style={{ display: 'block', color: 'var(--green-900)', fontSize: 'var(--text-base)', marginBottom: 4 }}>Recurso solar de la zona</strong>
                      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--green-800)', margin: 0 }}>Alicante · <span className="num">1.847 kWh/m²·año</span> · β óptimo 34°</p>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}

const pasosOnboarding = [
  { titulo: 'Crea un proyecto', desc: 'Ubicación, cubierta y consumo del cliente' },
  { titulo: 'Elige los equipos', desc: 'Paneles, inversor y baterías del catálogo' },
  { titulo: 'Revisa el análisis', desc: 'Producción, pérdidas y rentabilidad' },
  { titulo: 'Genera la memoria', desc: 'Memoria técnica firmable en PDF' },
]

function WelcomeCard({ onCreate }) {
  return (
    <Card className="sun-card--pad" style={{ maxWidth: 560, margin: '0 auto' }}>
      <div className="sun-empty">
        <div className="sun-empty__icon"><Icon name="sun" size={26} /></div>
        <div className="sun-empty__title">Bienvenido a Sunalyze</div>
        <div className="sun-empty__desc">De coordenadas a memoria técnica firmable en 10 minutos. Así funciona:</div>
        <ol style={{ listStyle: 'none', margin: 'var(--space-2) 0 0', padding: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', textAlign: 'left', width: '100%', maxWidth: 380 }}>
          {pasosOnboarding.map((paso, i) => (
            <li key={paso.titulo} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
              <span aria-hidden="true" style={{ flex: 'none', width: 26, height: 26, borderRadius: '50%', background: 'var(--surface-brand-soft)', color: 'var(--green-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--text-sm)', fontWeight: 'var(--fw-bold)' }}>{i + 1}</span>
              <span>
                <strong style={{ display: 'block', color: 'var(--text-strong)', fontSize: 'var(--text-base)' }}>{paso.titulo}</strong>
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>{paso.desc}</span>
              </span>
            </li>
          ))}
        </ol>
        <div className="sun-empty__actions">
          <Btn variant="primary" icon="plus" onClick={onCreate}>Crear tu primer proyecto</Btn>
        </div>
      </div>
    </Card>
  )
}

function buildKpis(projects) {
  const list = projects || []
  const activos = list.filter((p) => p.estado !== 'borrador').length
  const potencia = list.reduce((acc, p) => acc + (p.kwp || 0), 0)
  const memorias = list.filter((p) => p.estado === 'memoria').length
  const borradores = list.filter((p) => p.estado === 'borrador').length
  return [
    { label: 'Proyectos activos', value: activos, icon: 'folder', bg: 'var(--green-100)', fg: 'var(--green-700)' },
    { label: 'Potencia diseñada', value: dec(potencia), unit: 'kWp', icon: 'zap', bg: 'var(--amber-100)', fg: 'var(--amber-700)' },
    { label: 'Memorias', value: memorias, icon: 'file-check-2', bg: 'var(--blue-100)', fg: 'var(--blue-700)' },
    { label: 'Borradores', value: borradores, icon: 'pencil-ruler', bg: 'var(--ink-200)', fg: 'var(--ink-700)' },
  ]
}

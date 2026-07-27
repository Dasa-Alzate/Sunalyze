import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Topbar, Card, Btn, IconBtn, Field, SelectField, Spinner, ErrorState, Badge } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { useAuth } from '@/services/auth'
import { estadoMeta } from '@/shared/estados'

const CCAA_OPTIONS = [
  { value: '', label: 'Sin asignar' },
  { value: 'comunitat valenciana', label: 'Comunitat Valenciana' },
  { value: 'murcia', label: 'Región de Murcia' },
]

const TRANSITION_LABELS = {
  borrador: 'Volver a borrador',
  en_revision: 'Enviar a revisión',
  presentado: 'Marcar como presentado',
  aprobado: 'Marcar como aprobado',
  rechazado: 'Marcar como rechazado',
}

function copyText(text, label) {
  navigator.clipboard.writeText(text).then(
    () => toast('success', 'Copiado', label),
    () => toast('error', 'No se pudo copiar'),
  )
}

export default function LegalizationPanel() {
  const { id } = useParams()
  const nav = useNavigate()
  const { can } = useAuth()
  const canLegalize = can('project:legalize')
  const canSign = can('memoria:sign')

  const [project, setProject] = useState(null)
  const [summary, setSummary] = useState(null)
  const [guia, setGuia] = useState(null)
  const [presentacion, setPresentacion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [expediente, setExpediente] = useState({ numero: '', fecha: '' })

  async function loadCcaaData(projectId, ccaa) {
    if (!ccaa) { setGuia(null); setPresentacion(null); return }
    const [g, p] = await Promise.all([
      api.legalization.guia(projectId).catch(() => null),
      api.legalization.presentacion(projectId).catch(() => null),
    ])
    setGuia(g)
    setPresentacion(p)
  }

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [proj, sum] = await Promise.all([
        api.projects.get(Number(id)),
        api.legalization.get(Number(id)),
      ])
      setProject(proj)
      setSummary(sum)
      setExpediente({ numero: sum.expediente_numero || '', fecha: sum.expediente_fecha || '' })
      await loadCcaaData(Number(id), proj.ccaa)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  async function changeCcaa(e) {
    const ccaa = e.target.value || null
    setBusy(true)
    try {
      const proj = await api.projects.update(Number(id), { ccaa })
      setProject(proj)
      await loadCcaaData(Number(id), proj.ccaa)
      toast('success', 'Comunidad autónoma actualizada')
    } catch (err) {
      toast('error', 'No se pudo actualizar', err.message)
    } finally {
      setBusy(false)
    }
  }

  async function doTransition(toEstado) {
    setBusy(true)
    try {
      const sum = await api.legalization.transition(Number(id), { to_estado: toEstado })
      setSummary(sum)
      toast('success', 'Estado actualizado', estadoMeta(toEstado).label)
    } catch (err) {
      toast('error', 'Transición no permitida', err.message)
    } finally {
      setBusy(false)
    }
  }

  async function saveExpediente() {
    if (!expediente.numero.trim()) {
      toast('warning', 'Indica el número de expediente')
      return
    }
    setBusy(true)
    try {
      const sum = await api.legalization.expediente(Number(id), {
        numero: expediente.numero.trim(),
        fecha: expediente.fecha || null,
      })
      setSummary(sum)
      toast('success', 'Expediente registrado', sum.expediente_numero)
    } catch (err) {
      toast('error', 'No se pudo registrar', err.message)
    } finally {
      setBusy(false)
    }
  }

  async function descargarMtdOficial() {
    toast('info', 'Generando modelo oficial…')
    try {
      const blob = await api.legalization.mtdOficial(Number(id))
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `mtd-oficial-${id}.pdf`
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (err) {
      toast('error', 'No se pudo generar el modelo oficial', err.message)
    }
  }

  if (loading) return (<><Topbar title="Legalización" crumb="Proyectos" /><div className="sun-content"><Spinner label="Cargando…" /></div></>)
  if (error) return (<><Topbar title="Legalización" crumb="Proyectos" /><div className="sun-content"><ErrorState message={error} onRetry={load} /></div></>)

  const meta = estadoMeta(summary.estado)
  const transiciones = summary.transiciones_posibles || []

  return (
    <>
      <Topbar
        title="Legalización"
        crumb={project?.cliente || 'Proyectos'}
        actions={
          <>
            <Btn variant="secondary" icon="file-text" onClick={() => nav(`/app/memoria/${id}`)}>Memoria</Btn>
            {guia && (
              <Btn variant="primary" icon="download" onClick={descargarMtdOficial} disabled={!canSign}
                title={canSign ? undefined : 'Tu rol no permite generar documentos de la memoria'}>
                MTD modelo oficial
              </Btn>
            )}
          </>
        }
      />
      <div className="sun-content">
        <div style={{ display: 'grid', gap: 'var(--space-4)', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', alignItems: 'start' }}>

          <Card className="sun-card--pad">
            <h3 style={{ marginTop: 0 }}>Estado del expediente</h3>
            <p><Badge tone={meta.tone}>{meta.label}</Badge>{!summary.memoria_firmada && <span style={{ marginLeft: 'var(--space-3)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Memoria sin firmar</span>}</p>
            {transiciones.length > 0 && (
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {transiciones.map((t) => (
                  <Btn key={t} variant="secondary" disabled={!canLegalize || busy}
                    title={canLegalize ? undefined : 'Tu rol no permite cambiar el estado de legalización'}
                    onClick={() => doTransition(t)}>
                    {TRANSITION_LABELS[t] || t}
                  </Btn>
                ))}
              </div>
            )}
            <div style={{ marginTop: 'var(--space-4)' }}>
              <Field label="Nº de expediente de Industria" value={expediente.numero}
                onChange={(e) => setExpediente((v) => ({ ...v, numero: e.target.value }))} />
              <Field label="Fecha de presentación" type="date" value={expediente.fecha}
                onChange={(e) => setExpediente((v) => ({ ...v, fecha: e.target.value }))} />
              <Btn variant="primary" icon="save" disabled={!canLegalize || busy} onClick={saveExpediente}
                title={canLegalize ? undefined : 'Tu rol no permite registrar el expediente'}>
                Guardar expediente
              </Btn>
            </div>
          </Card>

          <Card className="sun-card--pad">
            <h3 style={{ marginTop: 0 }}>Comunidad autónoma</h3>
            <SelectField label="Dónde se tramita la instalación" value={project?.ccaa || ''}
              options={CCAA_OPTIONS} onChange={changeCcaa} disabled={busy} />
            {!project?.ccaa && (
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                Asigna la comunidad autónoma para ver la guía de tramitación, el asistente de
                presentación y el modelo oficial de MTD.
              </p>
            )}
            {guia && (
              <>
                <h4>{guia.nombre} — {guia.plataforma}</h4>
                <p style={{ fontSize: 'var(--text-sm)' }}>{guia.autenticacion}</p>
                <p style={{ fontSize: 'var(--text-sm)' }}>{guia.resultado}</p>
                <ol style={{ paddingLeft: '1.2em' }}>
                  {guia.pasos.map((paso, i) => <li key={i} style={{ marginBottom: 'var(--space-2)' }}>{paso}</li>)}
                </ol>
                <h4>Trámites y modelos oficiales</h4>
                <ul style={{ paddingLeft: '1.2em' }}>
                  {guia.procedimientos.map((proc) => (
                    <li key={proc.codigo} style={{ marginBottom: 'var(--space-2)' }}>
                      <a href={proc.url} target="_blank" rel="noreferrer">{proc.codigo}</a> — {proc.nombre}
                    </li>
                  ))}
                  {guia.impresos.map((imp) => (
                    <li key={imp.codigo} style={{ marginBottom: 'var(--space-2)' }}>
                      <a href={imp.url} target="_blank" rel="noreferrer">{imp.codigo}</a> — {imp.nombre}
                      {imp.generable && <> <Badge tone="success">Generable desde Sunalyze</Badge></>}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </Card>

          {presentacion && (
            <Card className="sun-card--pad" style={{ gridColumn: '1 / -1' }}>
              <h3 style={{ marginTop: 0 }}>Asistente de presentación</h3>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                Los datos del proyecto en el orden en que los pide el formulario de la sede
                electrónica. Copia cada valor mientras presentas; la firma y la presentación
                siguen siendo tuyas, con tu certificado.
              </p>
              <div style={{ display: 'grid', gap: 'var(--space-4)', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                {presentacion.secciones.map((sec) => (
                  <div key={sec.seccion}>
                    <h4>{sec.seccion}</h4>
                    {sec.campos.map((campo) => (
                      <div key={campo.label} style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)', padding: '2px 0', borderBottom: '1px solid var(--border-subtle, #eee)' }}>
                        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', flex: '1 1 55%' }}>{campo.label}</span>
                        <span style={{ flex: '1 1 45%', fontVariantNumeric: 'tabular-nums' }}>{campo.value ?? '—'}</span>
                        {campo.value != null && campo.value !== '' && (
                          <IconBtn icon="copy" label="Copiar" size="sm" onClick={() => copyText(String(campo.value), campo.label)} />
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </Card>
          )}

        </div>
      </div>
    </>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { SelectField, Spinner, ErrorState, Icon, Metric } from '@/shared/ui'
import { api } from '@/api/client'
import { num, int, pct } from '@/shared/format'
import { debounce } from '@/shared/debounce'

function CleanStudy({ project, results }) {
  if (!results) {
    return (
      <p style={{ color: 'var(--text-subtle)', textAlign: 'center', padding: 'var(--space-6)' }}>
        Calcula un estudio en la pestaña de supuestos para ver el resumen de ahorro.
      </p>
    )
  }
  const m = results.metrics || {}
  return (
    <div className="sun-page finance-study">
      <header style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Estudio de ahorro</h2>
        <p style={{ color: 'var(--text-muted)' }}>{project?.cliente || 'Cliente'}</p>
      </header>
      <div className="finance-kpis" role="group" aria-label="Resumen de ahorro">
        <Metric label="Ahorro anual estimado" value={num(results.annual_saving_year1_eur, 0)} unit="€" />
        <Metric label="Retorno de la inversión" value={num(m.payback_simple_years, 1)} unit="años" />
        <Metric label="Rentabilidad (TIR)" value={pct(m.irr, 1)} unit="%" />
        <Metric label="Ahorro a vida útil (VAN)" value={num(m.npv_eur, 0)} unit="€" />
        <Metric label="CO₂ evitado al año" value={int(m.co2_avoided_year1_kg)} unit="kg" />
        <Metric label="CO₂ evitado total" value={int(m.co2_avoided_lifetime_kg)} unit="kg" />
      </div>
    </div>
  )
}

export default function SavingsStudy({ project, results }) {
  const [templates, setTemplates] = useState(null)
  const [templateId, setTemplateId] = useState('')
  const [html, setHtml] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    Promise.all([
      api.templates.list('propuesta_comercial').catch(() => []),
      api.templates.bank('propuesta_comercial').catch(() => []),
    ])
      .then(([org, bank]) => {
        if (!alive) return
        const published = [...(org || []), ...(bank || [])].filter((t) => t.status === 'published' || t.is_system)
        setTemplates(published)
        setTemplateId(published[0]?.id ? String(published[0].id) : '')
      })
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [])

  const runPreview = useMemo(() => debounce((tid, pid) => {
    if (!tid || !pid) { setHtml(''); return }
    setLoading(true)
    setError(null)
    api.templates.preview(Number(tid), Number(pid))
      .then((res) => setHtml(res?.html || ''))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, 400), [])

  useEffect(() => {
    runPreview(templateId, project?.id)
    return () => runPreview.cancel()
  }, [templateId, project, runPreview])

  return (
    <div className="finance-savings-study">
      <div className="sun-section-title">
        <Icon name="presentation" size={15} />
        Estudio de ahorro (orientado a venta)
      </div>
      {templates && templates.length > 0 && (
        <SelectField
          label="Plantilla de propuesta comercial"
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
          options={templates.map((t) => ({ value: String(t.id), label: t.name }))}
        />
      )}
      {error ? (
        <ErrorState message={error} />
      ) : loading ? (
        <Spinner label="Generando estudio…" />
      ) : html ? (
        <div className="sun-page" dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <CleanStudy project={project} results={results} />
      )}
    </div>
  )
}

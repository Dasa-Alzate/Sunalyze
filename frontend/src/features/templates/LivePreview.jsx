import { useEffect, useMemo, useState } from 'react'
import { SelectField, Spinner, ErrorState, Icon } from '@/shared/ui'
import { api } from '@/api/client'
import { debounce } from '@/shared/debounce'

export default function LivePreview({ templateId, contentSignature }) {
  const [projects, setProjects] = useState(null)
  const [projectId, setProjectId] = useState('')
  const [html, setHtml] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    api.projects.list()
      .then((list) => {
        if (!alive) return
        setProjects(list || [])
        setProjectId((list && list[0]?.id) ? String(list[0].id) : '')
      })
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [])

  const runPreview = useMemo(() => debounce((tid, pid) => {
    if (!tid || !pid) { setHtml(''); return }
    setLoading(true)
    setError(null)
    api.templates.preview(tid, Number(pid))
      .then((res) => setHtml(res?.html || ''))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, 500), [])

  useEffect(() => {
    runPreview(templateId, projectId)
    return () => runPreview.cancel()
  }, [templateId, projectId, contentSignature, runPreview])

  return (
    <div className="sun-preview">
      <div className="sun-section-title">
        <Icon name="eye" size={15} />
        Vista previa en vivo
      </div>
      <SelectField
        label="Proyecto de muestra"
        value={projectId}
        onChange={(e) => setProjectId(e.target.value)}
        options={(projects || []).map((p) => ({ value: String(p.id), label: p.cliente || `Proyecto ${p.id}` }))}
      >
        {(projects && projects.length === 0) ? <option value="">Sin proyectos</option> : null}
      </SelectField>
      {error ? (
        <ErrorState message={error} />
      ) : loading ? (
        <Spinner label="Generando vista previa…" />
      ) : html ? (
        <div className="sun-page" dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <p style={{ color: 'var(--text-subtle)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: 'var(--space-6)' }}>
          Elige un proyecto y añade contenido para ver la vista previa.
        </p>
      )}
    </div>
  )
}

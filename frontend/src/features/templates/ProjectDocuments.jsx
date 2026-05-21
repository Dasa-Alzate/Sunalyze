import { useEffect, useState } from 'react'
import { SelectField, Btn, Spinner, ErrorState, Icon, Badge } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { num } from '@/shared/format'

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${num(bytes / 1024, 1)} KB`
  return `${num(bytes / (1024 * 1024), 1)} MB`
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString('es-ES')
}

export default function ProjectDocuments({ templateId, canManage }) {
  const [projects, setProjects] = useState(null)
  const [projectId, setProjectId] = useState('')
  const [documents, setDocuments] = useState(null)
  const [error, setError] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [downloadingId, setDownloadingId] = useState(null)

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

  useEffect(() => {
    if (!projectId) { setDocuments([]); return }
    let alive = true
    setError(null)
    api.templates.projectDocuments(Number(projectId))
      .then((list) => alive && setDocuments(list || []))
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [projectId])

  async function refresh() {
    if (!projectId) return
    try {
      const list = await api.templates.projectDocuments(Number(projectId))
      setDocuments(list || [])
    } catch (e) { setError(e.message) }
  }

  async function generate() {
    if (!projectId) return
    setGenerating(true)
    try {
      await api.templates.generate(templateId, Number(projectId))
      toast('success', 'Documento generado')
      await refresh()
    } catch (e) {
      toast('error', 'No se pudo generar', e.message)
    } finally {
      setGenerating(false)
    }
  }

  async function download(doc) {
    setDownloadingId(doc.id)
    try {
      const blob = await api.templates.downloadDocument(doc.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `documento-${doc.id}.pdf`
      document.body.appendChild(a)
      a.click()
      setTimeout(() => { a.remove(); URL.revokeObjectURL(url) }, 100)
    } catch (e) {
      toast('error', 'No se pudo descargar', e.message)
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <div className="sun-preview">
      <div className="sun-section-title">
        <Icon name="file-text" size={15} />
        Documentos generados
      </div>
      <SelectField
        label="Proyecto"
        value={projectId}
        onChange={(e) => setProjectId(e.target.value)}
        options={(projects || []).map((p) => ({ value: String(p.id), label: p.cliente || `Proyecto ${p.id}` }))}
      >
        {(projects && projects.length === 0) ? <option value="">Sin proyectos</option> : null}
      </SelectField>

      {canManage && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <Btn variant="primary" size="sm" icon="file-text" busy={generating} disabled={!projectId} onClick={generate}>
            Generar PDF
          </Btn>
        </div>
      )}

      {error ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : documents === null ? (
        <Spinner label="Cargando documentos…" />
      ) : documents.length === 0 ? (
        <p style={{ color: 'var(--text-subtle)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: 'var(--space-5)' }}>
          Este proyecto aún no tiene documentos generados.
        </p>
      ) : (
        <ul className="sun-speclist" style={{ listStyle: 'none', margin: 0, padding: 0, marginTop: 'var(--space-3)' }}>
          {documents.map((doc) => (
            <li key={doc.id} className="sun-card" style={{ padding: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', flexWrap: 'wrap' }}>
                  <strong>{doc.template_name || 'Documento'}</strong>
                  {doc.template_version != null && <Badge tone="neutral">v{doc.template_version}</Badge>}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
                  {formatDate(doc.generated_at || doc.created_at)} · {formatSize(doc.pdf_size_bytes)}
                </div>
              </div>
              <Btn
                variant="secondary"
                size="sm"
                icon="download"
                busy={downloadingId === doc.id}
                onClick={() => download(doc)}
              >
                Descargar
              </Btn>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

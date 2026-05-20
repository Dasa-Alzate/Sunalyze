import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Topbar, Btn, IconBtn, Icon, Field, Spinner, ErrorState, Badge } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import VariablePicker from './VariablePicker'
import LivePreview from './LivePreview'
import { kindLabel, STATUS_TONES } from './constants'

let localSeq = 0
function newSection() {
  localSeq += 1
  return { id: `s_${Date.now()}_${localSeq}`, type: 'text', title: '', body: '' }
}

export default function TemplateBuilder() {
  const { id } = useParams()
  const nav = useNavigate()
  const [template, setTemplate] = useState(null)
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [picker, setPicker] = useState(null)
  const [signature, setSignature] = useState(0)
  const bodyRefs = useRef({})

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    api.templates.get(Number(id))
      .then((tpl) => {
        if (!alive) return
        setTemplate(tpl)
        setSections(Array.isArray(tpl.content) ? tpl.content.map((s) => ({ ...s })) : [])
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [id])

  const readOnly = !!template && (template.is_system || template.org_id == null)

  function touch() { setSignature((n) => n + 1) }

  function updateSection(secId, patch) {
    setSections((list) => list.map((s) => (s.id === secId ? { ...s, ...patch } : s)))
    touch()
  }

  function addSection() {
    setSections((list) => [...list, newSection()])
    touch()
  }

  function removeSection(secId) {
    setSections((list) => list.filter((s) => s.id !== secId))
    touch()
  }

  function move(secId, delta) {
    setSections((list) => {
      const idx = list.findIndex((s) => s.id === secId)
      const next = idx + delta
      if (idx < 0 || next < 0 || next >= list.length) return list
      const copy = [...list]
      const [item] = copy.splice(idx, 1)
      copy.splice(next, 0, item)
      return copy
    })
    touch()
  }

  function insertVariable(secId, expression) {
    const el = bodyRefs.current[secId]
    setSections((list) => list.map((s) => {
      if (s.id !== secId) return s
      const body = s.body || ''
      const pos = el ? el.selectionStart : body.length
      const next = body.slice(0, pos) + expression + body.slice(el ? el.selectionEnd : body.length)
      return { ...s, body: next }
    }))
    touch()
  }

  async function save(publish) {
    setSaving(true)
    try {
      await api.templates.saveContent(Number(id), { content: sections, changelog: publish ? 'Publicación' : '' })
      if (publish) {
        const tpl = await api.templates.publish(Number(id))
        setTemplate((t) => ({ ...t, status: tpl.status }))
        toast('success', 'Plantilla publicada')
      } else {
        toast('success', 'Cambios guardados')
      }
      setSignature((n) => n + 1)
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return (<><Topbar title="Plantilla" crumb="Plantillas" /><div className="sun-content"><Spinner label="Cargando plantilla…" /></div></>)
  if (error) return (<><Topbar title="Plantilla" crumb="Plantillas" /><div className="sun-content"><ErrorState message={error} onRetry={() => nav(0)} /></div></>)

  const statusTone = STATUS_TONES[template?.status] || STATUS_TONES.draft

  return (
    <>
      <Topbar
        title={template?.name || 'Plantilla'}
        crumb="Plantillas"
        actions={
          !readOnly && (
            <>
              <Btn variant="secondary" icon="save" data-busy={saving} disabled={saving} onClick={() => save(false)}>Guardar</Btn>
              <Btn variant="primary" icon="send" disabled={saving} onClick={() => save(true)}>Publicar</Btn>
            </>
          )
        }
      />
      <div className="sun-content">
        <div className="sun-memoria">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
              <Badge tone="neutral">{kindLabel(template?.kind)}</Badge>
              <Badge tone={statusTone.tone}>{statusTone.label}</Badge>
              {readOnly && <Badge tone="neutral" icon="lock">Solo lectura</Badge>}
            </div>

            <div className="sun-memoria__sections">
              {sections.length === 0 && (
                <p style={{ color: 'var(--text-muted)' }}>Esta plantilla aún no tiene secciones.</p>
              )}
              {sections.map((s, i) => (
                <div key={s.id} className="sun-msection sun-msection--active">
                  <div className="sun-msection__head" style={{ cursor: 'default' }}>
                    <span className="sun-msection__title">Sección {i + 1}</span>
                    {!readOnly && (
                      <span style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--space-1)' }}>
                        <IconBtn icon="arrow-up" label="Subir sección" size="sm" disabled={i === 0} onClick={() => move(s.id, -1)} />
                        <IconBtn icon="arrow-down" label="Bajar sección" size="sm" disabled={i === sections.length - 1} onClick={() => move(s.id, 1)} />
                        <IconBtn icon="trash-2" label="Eliminar sección" size="sm" onClick={() => removeSection(s.id)} />
                      </span>
                    )}
                  </div>
                  <div className="sun-msection__body">
                    <div className="sun-speclist" style={{ marginTop: 'var(--space-3)' }}>
                      <Field
                        label="Título de la sección"
                        value={s.title || ''}
                        readOnly={readOnly}
                        onChange={(e) => updateSection(s.id, { title: e.target.value })}
                      />
                      <Field label="Cuerpo">
                        <textarea
                          ref={(el) => { bodyRefs.current[s.id] = el }}
                          className="sun-input"
                          rows={5}
                          readOnly={readOnly}
                          value={s.body || ''}
                          onChange={(e) => updateSection(s.id, { body: e.target.value })}
                          aria-label={`Cuerpo de la sección ${i + 1}`}
                        />
                      </Field>
                      {!readOnly && (
                        <Btn variant="secondary" size="sm" icon="braces" onClick={() => setPicker(s.id)}>
                          Insertar variable
                        </Btn>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {!readOnly && (
              <div style={{ marginTop: 'var(--space-5)' }}>
                <Btn variant="secondary" icon="plus" onClick={addSection}>Añadir sección</Btn>
              </div>
            )}
          </div>

          <LivePreview templateId={Number(id)} contentSignature={signature} />
        </div>
      </div>

      {picker && (
        <VariablePicker
          kind={template?.kind}
          onInsert={(expr) => insertVariable(picker, expr)}
          onClose={() => setPicker(null)}
        />
      )}
    </>
  )
}

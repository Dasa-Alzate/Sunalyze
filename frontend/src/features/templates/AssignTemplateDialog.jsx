import { useState } from 'react'
import { Scrim, Btn, Field, Icon, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

export default function AssignTemplateDialog({ installation, categories, labels, onClose, onSaved }) {
  const [categoryId, setCategoryId] = useState(installation.category?.id ? String(installation.category.id) : '')
  const [labelIds, setLabelIds] = useState(new Set((installation.labels || []).map((l) => l.id)))
  const [localCategories, setLocalCategories] = useState(categories)
  const [localLabels, setLocalLabels] = useState(labels)
  const [newCategory, setNewCategory] = useState('')
  const [newLabel, setNewLabel] = useState('')
  const [busy, setBusy] = useState(false)

  function toggleLabel(id) {
    setLabelIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function addCategory() {
    const name = newCategory.trim()
    if (!name) return
    try {
      const cat = await api.templates.createCategory(name)
      setLocalCategories((list) => [...list, cat])
      setCategoryId(String(cat.id))
      setNewCategory('')
    } catch (e) { toast('error', 'No se pudo crear la categoría', e.message) }
  }

  async function addLabel() {
    const name = newLabel.trim()
    if (!name) return
    try {
      const label = await api.templates.createLabel(name)
      setLocalLabels((list) => [...list, label])
      setLabelIds((prev) => new Set(prev).add(label.id))
      setNewLabel('')
    } catch (e) { toast('error', 'No se pudo crear la etiqueta', e.message) }
  }

  async function submit() {
    setBusy(true)
    try {
      await api.templates.setCategory(installation.id, categoryId ? Number(categoryId) : null)
      await api.templates.setLabels(installation.id, Array.from(labelIds))
      toast('success', 'Organización guardada')
      onSaved()
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
    } finally {
      setBusy(false)
    }
  }

  const title = installation.template?.name || 'Plantilla'

  return (
    <Scrim label={`Organizar ${title}`} onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>Organizar plantilla</h3></header>
        <div className="sun-drawer__body">
          {busy ? <Spinner label="Guardando…" /> : (
            <div className="sun-speclist">
              <fieldset className="sun-field" style={{ border: 0, padding: 0, margin: 0 }}>
                <legend className="sun-field__label">Categoría</legend>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                  <label style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                    <input
                      type="radio"
                      name="assign-category"
                      checked={categoryId === ''}
                      onChange={() => setCategoryId('')}
                    />
                    Sin categoría
                  </label>
                  {localCategories.map((c) => (
                    <label key={c.id} style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                      <input
                        type="radio"
                        name="assign-category"
                        value={String(c.id)}
                        checked={categoryId === String(c.id)}
                        onChange={() => setCategoryId(String(c.id))}
                      />
                      {c.name}
                    </label>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                  <Field
                    label="Nueva categoría"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                  />
                  <Btn variant="secondary" size="sm" icon="plus" onClick={addCategory} disabled={!newCategory.trim()}>Crear</Btn>
                </div>
              </fieldset>

              <fieldset className="sun-field" style={{ border: 0, padding: 0, margin: 0 }}>
                <legend className="sun-field__label">Etiquetas</legend>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                  {localLabels.length === 0 && <span style={{ color: 'var(--text-muted)' }}>Sin etiquetas todavía.</span>}
                  {localLabels.map((l) => (
                    <label key={l.id} style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                      <input
                        type="checkbox"
                        checked={labelIds.has(l.id)}
                        onChange={() => toggleLabel(l.id)}
                      />
                      <Icon name="tag" size={13} />{l.name}
                    </label>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                  <Field
                    label="Nueva etiqueta"
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                  />
                  <Btn variant="secondary" size="sm" icon="plus" onClick={addLabel} disabled={!newLabel.trim()}>Crear</Btn>
                </div>
              </fieldset>
            </div>
          )}
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="save" busy={busy} onClick={submit}>Guardar</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

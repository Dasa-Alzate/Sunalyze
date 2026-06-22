import { useEffect, useMemo, useState } from 'react'
import { Scrim, Btn, Field, SelectField, Spinner, ErrorState, Icon } from '@/shared/ui'
import { api } from '@/api/client'
import { FILTERS, buildExpression } from './constants'

export default function VariablePicker({ kind, onInsert, onClose }) {
  const [groups, setGroups] = useState(null)
  const [error, setError] = useState(null)
  const [entity, setEntity] = useState('')
  const [path, setPath] = useState('')
  const [filterValue, setFilterValue] = useState('')
  const [argValues, setArgValues] = useState({})

  useEffect(() => {
    let alive = true
    setError(null)
    setGroups(null)
    api.templates.variables(kind)
      .then((g) => { if (alive) { setGroups(g); setEntity(g[0]?.entity || '') } })
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [kind])

  const activeGroup = useMemo(
    () => (groups || []).find((g) => g.entity === entity) || null,
    [groups, entity],
  )

  useEffect(() => {
    if (activeGroup) setPath(activeGroup.vars[0]?.path || '')
  }, [activeGroup])

  const filterDef = FILTERS.find((f) => f.value === filterValue)
  const preview = path ? buildExpression(path, filterValue, argValues) : ''

  function confirm() {
    if (!path) return
    onInsert(preview)
    onClose()
  }

  return (
    <Scrim label="Insertar variable" onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head">
          <h3>Insertar variable</h3>
        </header>
        <div className="sun-drawer__body">
          {error ? (
            <ErrorState message={error} />
          ) : groups === null ? (
            <Spinner label="Cargando variables…" />
          ) : groups.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No hay variables disponibles para este tipo de documento.</p>
          ) : (
            <div className="sun-speclist">
              <SelectField
                label="Entidad"
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                options={groups.map((g) => ({ value: g.entity, label: g.label }))}
              />
              <SelectField
                label="Propiedad"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                options={(activeGroup?.vars || []).map((v) => ({ value: v.path, label: `${v.label} (${v.tipo})` }))}
              />
              <SelectField
                label="Formato"
                value={filterValue}
                onChange={(e) => { setFilterValue(e.target.value); setArgValues({}) }}
                options={FILTERS.map((f) => ({ value: f.value, label: f.label }))}
              />
              {(filterDef?.args || []).map((a) => (
                <Field
                  key={a.key}
                  label={a.label}
                  type="number"
                  numeric
                  value={argValues[a.key] ?? a.default}
                  onChange={(e) => setArgValues((v) => ({ ...v, [a.key]: e.target.value }))}
                />
              ))}
              {preview && (
                <div className="sun-section-title" style={{ marginTop: 'var(--space-2)' }}>
                  <Icon name="code" size={14} />
                  <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-brand)' }}>{preview}</code>
                </div>
              )}
            </div>
          )}
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="plus" onClick={confirm} disabled={!path}>Insertar</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

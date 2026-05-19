import { useEffect, useState } from 'react'
import { Topbar } from '@/shared/ui'
import { Btn, IconBtn, Icon, Badge, Field, SelectField, Spinner, ErrorState, Scrim } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

function globalOverride(flag) {
  return flag.overrides.find((o) => o.scope === 'global') || null
}

function effectiveGlobal(flag) {
  const g = globalOverride(flag)
  return g ? g.enabled : flag.default_enabled
}

export default function Flags() {
  const [flags, setFlags] = useState(null)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const [target, setTarget] = useState(null)

  function load() {
    setError(null)
    setFlags(null)
    api.admin.flags().then(setFlags).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  async function setGlobal(flag, enabled) {
    try {
      await api.admin.setOverride(flag.key, { scope: 'global', enabled })
      toast('success', `${flag.key} → global ${enabled ? 'ON' : 'OFF'}`)
      load()
    } catch (e) { toast('error', 'No se pudo aplicar', e.message) }
  }

  async function clearGlobal(flag) {
    try {
      await api.admin.clearOverride(flag.key, { scope: 'global' })
      toast('info', `${flag.key} → vuelve al default (${flag.default_enabled ? 'ON' : 'OFF'})`)
      load()
    } catch (e) { toast('error', 'No se pudo limpiar', e.message) }
  }

  async function createFlag(values) {
    if (!values.key.trim() || !values.nombre.trim()) { toast('error', 'Faltan key y nombre'); return }
    try {
      await api.admin.upsertFlag({
        key: values.key.trim(), nombre: values.nombre.trim(),
        titulo: values.titulo, descripcion: values.descripcion,
        default_enabled: values.default_enabled === 'on',
        is_visible: values.is_visible === 'on',
        image_path: values.image_path || null,
        thumbnail_path: values.thumbnail_path || null,
        help_url: values.help_url || null,
        price: values.price === '' ? null : Number(values.price),
      })
      toast('success', 'Flag guardado', values.key)
      setCreating(false)
      load()
    } catch (e) { toast('error', 'No se pudo crear', e.message) }
  }

  return (
    <>
      <Topbar
        title="Feature flags"
        crumb="Plataforma"
        actions={<Btn variant="primary" icon="plus" onClick={() => setCreating(true)}>Nuevo flag</Btn>}
      />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : flags === null ? (
          <Spinner label="Cargando flags…" />
        ) : flags.length === 0 ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="flag" size={26} /></div>
            <div className="sun-empty__title">Sin flags</div>
            <div className="sun-empty__desc">Crea el primer feature flag para gatear funcionalidad.</div>
            <div className="sun-empty__actions"><Btn variant="primary" icon="plus" onClick={() => setCreating(true)}>Nuevo flag</Btn></div>
          </div>
        ) : (
          <div className="sun-card" style={{ overflow: 'hidden' }}>
            <table className="sun-table">
              <thead>
                <tr>
                  <th>Flag</th>
                  <th>Default</th>
                  <th>Global</th>
                  <th>Overrides</th>
                  <th style={{ width: 220 }}></th>
                </tr>
              </thead>
              <tbody>
                {flags.map((f) => {
                  const eff = effectiveGlobal(f)
                  const scoped = f.overrides.filter((o) => o.scope !== 'global')
                  return (
                    <tr key={f.key}>
                      <td>
                        <div className="sun-cell-client">
                          <strong>{f.key}</strong>
                          <span>{f.nombre}</span>
                        </div>
                      </td>
                      <td><Badge tone={f.default_enabled ? 'brand' : 'neutral'}>{f.default_enabled ? 'ON' : 'OFF'}</Badge></td>
                      <td>
                        <span className="sun-cell-status">
                          <Dot on={eff} />
                          <span style={{ fontSize: 'var(--text-sm)' }}>{eff ? 'ON' : 'OFF'}</span>
                          {globalOverride(f) && <Badge tone="warning">override</Badge>}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>{scoped.length ? `${scoped.length} por org/usuario` : '—'}</td>
                      <td>
                        <span style={{ display: 'inline-flex', gap: 6, justifyContent: 'flex-end', width: '100%' }}>
                          <Btn variant="secondary" size="sm" onClick={() => setGlobal(f, !eff)}>{eff ? 'Apagar' : 'Encender'}</Btn>
                          {globalOverride(f) && <Btn variant="ghost" size="sm" onClick={() => clearGlobal(f)}>Default</Btn>}
                          <IconBtn icon="sliders-horizontal" label="Overrides por org/usuario" size="sm" onClick={() => setTarget(f)} />
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {creating && <CreateFlagDrawer onClose={() => setCreating(false)} onSave={createFlag} />}
        {target && <OverridesDrawer flag={target} onClose={() => setTarget(null)} onChanged={load} />}
      </div>
    </>
  )
}

function Dot({ on }) {
  return <span className={`sun-statusdot sun-statusdot--${on ? 'valid' : 'pending'}`} />
}

function CreateFlagDrawer({ onClose, onSave }) {
  const [v, setV] = useState({
    key: '', nombre: '', titulo: '', descripcion: '', default_enabled: 'off',
    is_visible: 'off', image_path: '', thumbnail_path: '', help_url: '', price: '',
  })
  const set = (k) => (e) => setV((s) => ({ ...s, [k]: e.target.value }))
  return (
    <Scrim onClose={onClose} label="Nuevo flag / módulo">
      <div className="sun-drawer">
        <div className="sun-drawer__head"><h3>Nuevo flag / módulo</h3><IconBtn icon="x" label="Cerrar" onClick={onClose} /></div>
        <div className="sun-drawer__body">
          <Field label="Key (estable, minúsculas)" required placeholder="advanced_export" value={v.key} onChange={set('key')} />
          <Field label="Nombre interno" required placeholder="Exportación avanzada" value={v.nombre} onChange={set('nombre')} />
          <SelectField label="Default" value={v.default_enabled} onChange={set('default_enabled')}
            options={[{ value: 'off', label: 'OFF (apagado por defecto)' }, { value: 'on', label: 'ON (encendido por defecto)' }]} />

          <div className="sun-divider">Marketplace (visible al usuario)</div>
          <SelectField label="¿Visible en el marketplace?" value={v.is_visible} onChange={set('is_visible')}
            options={[{ value: 'off', label: 'No (flag interno)' }, { value: 'on', label: 'Sí (módulo público)' }]} />
          <Field label="Título" placeholder="Exportación avanzada" value={v.titulo} onChange={set('titulo')} />
          <Field label="Descripción" value={v.descripcion} onChange={set('descripcion')} />
          <div className="sun-speclist">
            <Field label="Precio (€/mes, 0 = incluido)" numeric type="number" step="any" value={v.price} onChange={set('price')} />
            <Field label="Enlace de ayuda" placeholder="https://…" value={v.help_url} onChange={set('help_url')} />
            <Field label="Imagen (path/URL)" placeholder="/static/…" value={v.image_path} onChange={set('image_path')} />
            <Field label="Miniatura (path/URL)" placeholder="/static/…" value={v.thumbnail_path} onChange={set('thumbnail_path')} />
          </div>
        </div>
        <div className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="check" onClick={() => onSave(v)}>Guardar</Btn>
        </div>
      </div>
    </Scrim>
  )
}

function OverridesDrawer({ flag, onClose, onChanged }) {
  const [scope, setScope] = useState('org')
  const [targets, setTargets] = useState({ org: null, user: null })
  const [targetId, setTargetId] = useState('')
  const [enabled, setEnabled] = useState('on')
  const [overrides, setOverrides] = useState(flag.overrides.filter((o) => o.scope !== 'global'))

  useEffect(() => {
    api.admin.organizations().then((o) => setTargets((t) => ({ ...t, org: o }))).catch(() => {})
    api.admin.users().then((u) => setTargets((t) => ({ ...t, user: u }))).catch(() => {})
  }, [])

  const list = targets[scope] || []
  const labelOf = (o) => {
    const arr = targets[o.scope] || []
    const found = arr.find((x) => x.id === o.scope_id)
    return found ? (found.nombre || found.email) : `#${o.scope_id}`
  }

  async function add() {
    if (!targetId) { toast('warning', 'Elige un destino'); return }
    try {
      await api.admin.setOverride(flag.key, { scope, scope_id: Number(targetId), enabled: enabled === 'on' })
      toast('success', 'Override aplicado')
      const fresh = await api.admin.flags()
      const f = fresh.find((x) => x.key === flag.key)
      setOverrides((f?.overrides || []).filter((o) => o.scope !== 'global'))
      onChanged()
    } catch (e) { toast('error', 'No se pudo aplicar', e.message) }
  }

  async function remove(o) {
    try {
      await api.admin.clearOverride(flag.key, { scope: o.scope, scope_id: o.scope_id })
      setOverrides((prev) => prev.filter((x) => x !== o))
      onChanged()
    } catch (e) { toast('error', 'No se pudo quitar', e.message) }
  }

  return (
    <Scrim onClose={onClose} label={`Overrides · ${flag.key}`}>
      <div className="sun-drawer">
        <div className="sun-drawer__head"><h3>Overrides · {flag.key}</h3><IconBtn icon="x" label="Cerrar" onClick={onClose} /></div>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <SelectField label="Ámbito" value={scope} onChange={(e) => { setScope(e.target.value); setTargetId('') }}
              options={[{ value: 'org', label: 'Organización' }, { value: 'user', label: 'Usuario' }]} />
            <SelectField label="Estado" value={enabled} onChange={(e) => setEnabled(e.target.value)}
              options={[{ value: 'on', label: 'ON' }, { value: 'off', label: 'OFF' }]} />
          </div>
          <SelectField label="Destino" value={targetId} onChange={(e) => setTargetId(e.target.value)}
            options={[{ value: '', label: '— elegir —' }, ...list.map((x) => ({ value: x.id, label: x.nombre || x.email }))]} />
          <Btn variant="primary" icon="plus" onClick={add}>Aplicar override</Btn>

          <div className="sun-divider">Overrides activos</div>
          {overrides.length === 0 ? (
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Ninguno.</p>
          ) : overrides.map((o) => (
            <div key={`${o.scope}-${o.scope_id}`} className="sun-projrow" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0' }}>
              <span style={{ fontSize: 'var(--text-sm)' }}>{o.scope === 'org' ? 'Org' : 'Usuario'}: <strong>{labelOf(o)}</strong></span>
              <span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                <Badge tone={o.enabled ? 'brand' : 'neutral'}>{o.enabled ? 'ON' : 'OFF'}</Badge>
                <IconBtn icon="trash-2" label="Quitar" size="sm" onClick={() => remove(o)} />
              </span>
            </div>
          ))}
        </div>
        <div className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cerrar</Btn>
        </div>
      </div>
    </Scrim>
  )
}

import { useEffect, useState } from 'react'
import { Topbar } from '@/shared/ui'
import { Btn, IconBtn, Icon, Badge, Field, SelectField, ExportMenu, Spinner, ErrorState, Scrim } from '@/shared/ui'
import { api } from '@/api/client'
import { dec } from '@/shared/format'
import { exportRows } from '@/services/export'
import { toast } from '@/services/toast'
import { useAuth } from '@/services/auth'

const SCHEMAS = {
  panels: {
    label: 'Paneles', singular: 'panel', icon: 'square', resource: 'panels',
    columns: [
      { key: 'nombre', label: 'Nombre', name: true },
      { key: 'power', label: 'W', num: true },
      { key: 'voc', label: 'Voc', num: true },
      { key: 'vmp', label: 'Vmp', num: true },
      { key: 'imp', label: 'Imp', num: true },
      { key: 'dim', label: 'Dim. (mm)', render: (r) => `${r.width || 0}×${r.height || 0}` },
    ],
    fields: [
      { key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: LONGi Hi-MO6 550W' },
      { key: 'power', label: 'Potencia (W)', num: true, required: true },
      { key: 'voc', label: 'Voc (V)', num: true, required: true },
      { key: 'vmp', label: 'Vmp (V)', num: true, required: true },
      { key: 'imp', label: 'Imp (A)', num: true, required: true },
      { key: 'isc', label: 'Isc (A)', num: true },
      { key: 'y', label: 'Eficiencia (%)', num: true },
      { key: 'tcp', label: 'Coef. temp. potencia (%/°C)', num: true },
      { key: 'tcv', label: 'Coef. temp. voltaje (%/°C)', num: true },
      { key: 't_noct', label: 'NOCT (°C)', num: true },
      { key: 'width', label: 'Ancho (mm)', num: true },
      { key: 'height', label: 'Alto (mm)', num: true },
      { key: 'datasheet', label: 'Ficha técnica (URL)', placeholder: 'https://…' },
    ],
  },
  inverters: {
    label: 'Inversores', singular: 'inversor', icon: 'plug-zap', resource: 'inverters',
    columns: [
      { key: 'nombre', label: 'Nombre', name: true },
      { key: 'power', label: 'kW', num: true },
      { key: 'power_max', label: 'P. máx', num: true },
      { key: 'vmax', label: 'Vmax', num: true },
      { key: 'I_max_input', label: 'I máx in', num: true },
      { key: 'I_max_output', label: 'I máx out', num: true },
    ],
    fields: [
      { key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: Fronius PRIMO 5.0-1' },
      { key: 'power', label: 'Potencia AC (kW)', num: true, required: true },
      { key: 'power_max', label: 'Potencia máx DC (kW)', num: true },
      { key: 'vmax', label: 'Vmax (V)', num: true, required: true },
      { key: 'I_max_input', label: 'I máx entrada (A)', num: true, required: true },
      { key: 'I_max_output', label: 'I máx salida (A)', num: true, required: true },
      { key: 'y', label: 'Eficiencia (%)', num: true },
    ],
  },
  batteries: {
    label: 'Baterías', singular: 'batería', icon: 'battery-charging', resource: 'batteries',
    columns: [
      { key: 'nombre', label: 'Nombre', name: true },
      { key: 'capacity_kwh', label: 'kWh', num: true },
      { key: 'usable_kwh', label: 'kWh útil', num: true },
      { key: 'power_kw', label: 'kW', num: true },
      { key: 'voltage', label: 'V', num: true },
      { key: 'technology', label: 'Tecnología' },
    ],
    fields: [
      { key: 'nombre', label: 'Nombre', required: true, placeholder: 'Ej: BYD HVS 5.1' },
      { key: 'capacity_kwh', label: 'Capacidad nominal (kWh)', num: true, required: true },
      { key: 'usable_kwh', label: 'Capacidad útil (kWh)', num: true },
      { key: 'dod', label: 'Profundidad de descarga (%)', num: true },
      { key: 'power_kw', label: 'Potencia (kW)', num: true, required: true },
      { key: 'voltage', label: 'Voltaje (V)', num: true, required: true },
      { key: 'technology', label: 'Tecnología', placeholder: 'Ej: LiFePO4' },
      { key: 'round_trip_efficiency', label: 'Eficiencia ida y vuelta (%)', num: true },
      { key: 'max_cycles', label: 'Ciclos máximos', num: true },
    ],
  },
  wires: {
    label: 'Cables', singular: 'cable', icon: 'cable', resource: 'wires',
    columns: [
      { key: 'tipo', label: 'Tipo', name: true },
      { key: 'material', label: 'Material' },
      { key: 'seccion', label: 'Sección mm²', num: true },
      { key: 'corriente', label: 'I máx (A)', num: true },
      { key: 'no_conductores', label: 'Nº cond.', num: true },
    ],
    fields: [
      { key: 'tipo', label: 'Tipo', required: true, placeholder: 'Ej: B1' },
      { key: 'material', label: 'Material', select: ['Cu', 'Al'], required: true },
      { key: 'seccion', label: 'Sección (mm²)', num: true, required: true },
      { key: 'corriente', label: 'I máx admisible (A)', num: true, required: true },
      { key: 'no_conductores', label: 'Nº de conductores', num: true, required: true },
    ],
  },
}

const TAB_ORDER = ['panels', 'inverters', 'batteries', 'wires']

export default function EquipmentLibrary() {
  const { can } = useAuth()
  const canEdit = can('equipment:edit')
  const canManage = can('catalog:manage')
  const canSubscribe = can('catalog:subscribe')
  const [tab, setTab] = useState('panels')
  const [data, setData] = useState({ panels: null, inverters: null, batteries: null, wires: null })
  const [catalogs, setCatalogs] = useState(null)
  const [market, setMarket] = useState(null)
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(null)
  const [newCatalog, setNewCatalog] = useState(false)
  const [filter, setFilter] = useState('todos')

  const isMarket = tab === 'marketplace'
  const schema = isMarket ? null : SCHEMAS[tab]
  const rows = isMarket ? null : data[tab]
  const ownCatalogs = (catalogs || []).filter((c) => c.own)

  function loadCatalogs() {
    api.catalogs.list().then(setCatalogs).catch((e) => setError(e.message))
  }
  function loadMarket() {
    setMarket(null)
    api.marketplace.list().then(setMarket).catch((e) => setError(e.message))
  }
  function loadEquipment(which = tab) {
    setError(null)
    setData((d) => ({ ...d, [which]: null }))
    api[SCHEMAS[which].resource].list()
      .then((res) => setData((d) => ({ ...d, [which]: res })))
      .catch((e) => setError(e.message))
  }
  function invalidateEquipment() {
    setData({ panels: null, inverters: null, batteries: null, wires: null })
  }

  useEffect(loadCatalogs, [])
  useEffect(() => {
    if (isMarket) {
      if (market === null) loadMarket()
    } else if (data[tab] === null) {
      loadEquipment(tab)
    }
  }, [tab])

  const counts = TAB_ORDER.reduce((acc, t) => {
    acc[t] = (catalogs || []).reduce((sum, c) => sum + ((c.counts && c.counts[t]) || 0), 0)
    return acc
  }, {})
  const visibleRows = (rows || []).filter((r) => filter === 'todos' || String(r.catalog_id) === String(filter))

  async function save(values) {
    const body = {}
    schema.fields.forEach((f) => {
      let v = values[f.key]
      if (f.num && v !== '' && v != null) v = Number(v)
      if (v !== '' && v != null) body[f.key] = v
    })
    const movable = !editing.id || editing.deletable
    if (movable && values.catalog_id) body.catalog_id = Number(values.catalog_id)
    const missing = schema.fields.filter((f) => f.required && (body[f.key] === undefined || body[f.key] === ''))
    if (missing.length) {
      toast('error', 'Faltan campos', missing.map((f) => f.label).join(', '))
      return
    }
    try {
      if (editing.id) {
        await api[schema.resource].update(editing.id, body)
        toast('success', `${schema.singular} actualizado`)
      } else {
        await api[schema.resource].create(body)
        toast('success', `${schema.singular} añadido`)
      }
      setEditing(null)
      loadEquipment()
      loadCatalogs()
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
    }
  }

  async function remove(row) {
    const name = row.nombre || `${row.tipo} ${row.seccion}mm²`
    if (!window.confirm(`¿Eliminar ${name}?`)) return
    try {
      await api[schema.resource].remove(row.id)
      toast('success', 'Eliminado')
      loadEquipment()
      loadCatalogs()
    } catch (e) {
      toast('error', 'No se pudo eliminar', e.message)
    }
  }

  async function toggleSubscription(cat) {
    try {
      if (cat.subscribed) {
        await api.catalogs.unsubscribe(cat.id)
        toast('info', 'Catálogo quitado', `${cat.nombre} ya no aparece en tu biblioteca`)
      } else {
        await api.catalogs.subscribe(cat.id)
        toast('success', 'Catálogo añadido', `${cat.nombre} disponible en tu biblioteca`)
      }
      loadMarket()
      loadCatalogs()
      invalidateEquipment()
    } catch (e) {
      toast('error', 'No se pudo actualizar', e.message)
    }
  }

  async function createCatalog(values) {
    if (!values.nombre.trim()) { toast('error', 'Falta el nombre'); return }
    try {
      await api.catalogs.create({ nombre: values.nombre, descripcion: values.descripcion })
      toast('success', 'Catálogo creado', values.nombre)
      setNewCatalog(false)
      loadCatalogs()
      loadMarket()
    } catch (e) {
      toast('error', 'No se pudo crear', e.message)
    }
  }

  async function removeCatalog(cat) {
    const c = cat.counts || {}
    const total = (c.panels || 0) + (c.inverters || 0) + (c.batteries || 0) + (c.wires || 0)
    if (!window.confirm(`¿Eliminar el catálogo «${cat.nombre}»? Se borrarán sus ${total} equipos.`)) return
    try {
      await api.catalogs.remove(cat.id)
      toast('success', 'Catálogo eliminado')
      loadCatalogs()
      loadMarket()
      invalidateEquipment()
    } catch (e) {
      toast('error', 'No se pudo eliminar', e.message)
    }
  }

  function exportCurrent(fmt) {
    const headers = [...schema.columns.map((c) => c.label), 'Catálogo']
    const out = visibleRows.map((r) => [...schema.columns.map((c) => (c.render ? c.render(r) : r[c.key])), r.catalog_nombre || ''])
    exportRows(fmt, schema.resource, headers, out)
  }

  const countsLabel = (cat) => {
    const c = cat.counts || {}
    return [
      c.panels ? `${c.panels} paneles` : null,
      c.inverters ? `${c.inverters} inversores` : null,
      c.batteries ? `${c.batteries} baterías` : null,
      c.wires ? `${c.wires} cables` : null,
    ].filter(Boolean).join(' · ') || 'Vacío'
  }

  return (
    <>
      <Topbar title="Equipos" crumb="Biblioteca" />
      <div className="sun-content">
        <div className="sun-tabs" role="tablist" style={{ marginBottom: 'var(--space-5)' }}>
          {TAB_ORDER.map((t) => (
            <button key={t} className={`sun-tab${tab === t ? ' sun-tab--active' : ''}`} onClick={() => setTab(t)}>
              <Icon name={SCHEMAS[t].icon} size={16} />{SCHEMAS[t].label}<span className="sun-tab__count">{counts[t]}</span>
            </button>
          ))}
          <button className={`sun-tab${isMarket ? ' sun-tab--active' : ''}`} onClick={() => setTab('marketplace')}>
            <Icon name="store" size={16} />Marketplace
          </button>
          {!isMarket && (
            <div style={{ marginLeft: 'auto', alignSelf: 'center', display: 'flex', gap: 'var(--space-3)' }}>
              <ExportMenu onExport={exportCurrent} />
              {canEdit && <Btn variant="primary" icon="plus" onClick={() => setEditing({})}>Añadir {schema.singular}</Btn>}
            </div>
          )}
          {isMarket && (
            <div style={{ marginLeft: 'auto', alignSelf: 'center' }}>
              {canManage && <Btn variant="primary" icon="plus" onClick={() => setNewCatalog(true)}>Nuevo catálogo</Btn>}
            </div>
          )}
        </div>

        {error ? (
          <ErrorState message={error} onRetry={() => { setError(null); isMarket ? loadMarket() : loadEquipment() }} />
        ) : isMarket ? (
          <MarketplaceView
            market={market}
            ownCatalogs={ownCatalogs}
            countsLabel={countsLabel}
            canManage={canManage}
            canSubscribe={canSubscribe}
            onToggle={toggleSubscription}
            onRemoveCatalog={removeCatalog}
          />
        ) : rows === null ? (
          <Spinner label={`Cargando ${schema.label.toLowerCase()}…`} />
        ) : (
          <>
            <div className="sun-toolbar">
              <select className="sun-select" style={{ width: 240 }} value={filter} onChange={(e) => setFilter(e.target.value)}>
                <option value="todos">Todos los catálogos</option>
                {(catalogs || []).map((c) => <option key={c.id} value={c.id}>{c.nombre}{c.own ? ' (propio)' : ''}</option>)}
              </select>
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                {visibleRows.length} de {rows.length}
              </span>
            </div>
            {visibleRows.length === 0 ? (
              <div className="sun-empty">
                <div className="sun-empty__icon"><Icon name={schema.icon} size={26} /></div>
                <div className="sun-empty__title">Sin {schema.label.toLowerCase()}</div>
                <div className="sun-empty__desc">Añade {schema.label.toLowerCase()} a tu catálogo o suscríbete a un catálogo del marketplace.</div>
                <div className="sun-empty__actions">
                  {canEdit && <Btn variant="primary" icon="plus" onClick={() => setEditing({})}>Añadir {schema.singular}</Btn>}
                  <Btn variant="secondary" icon="store" onClick={() => setTab('marketplace')}>Ir al marketplace</Btn>
                </div>
              </div>
            ) : (
              <div className="sun-card" style={{ overflow: 'hidden' }}>
                <table className="sun-table">
                  <thead>
                    <tr>
                      {schema.columns.map((c) => <th key={c.key} style={c.num ? { textAlign: 'right' } : undefined}>{c.label}</th>)}
                      <th>Catálogo</th>
                      <th style={{ width: 80 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleRows.map((r) => (
                      <tr key={r.id}>
                        {schema.columns.map((c) => (
                          <td
                            key={c.key}
                            className={[c.num ? 'num' : '', c.name ? 'sun-table__name' : ''].filter(Boolean).join(' ')}
                            style={c.num ? { textAlign: 'right' } : (!c.name ? { color: 'var(--text-muted)' } : undefined)}
                          >
                            {c.render ? c.render(r) : c.num ? dec(r[c.key]) : r[c.key]}
                          </td>
                        ))}
                        <td>
                          <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                            <Badge tone={r.deletable ? 'brand' : 'neutral'} icon={r.deletable ? 'user' : 'store'}>
                              {r.catalog_nombre || '—'}
                            </Badge>
                            {r.scraped && <Badge tone="accent" icon="bot">Scraped</Badge>}
                          </span>
                        </td>
                        <td>
                          {r.editable && canEdit ? (
                            <span style={{ display: 'inline-flex', gap: 4 }}>
                              <IconBtn icon="pencil" label="Editar" size="sm" onClick={() => setEditing(r)} />
                              {r.deletable && <IconBtn icon="trash-2" label="Eliminar" size="sm" onClick={() => remove(r)} />}
                            </span>
                          ) : (
                            <span title="Equipo del marketplace (solo lectura)" style={{ color: 'var(--text-subtle)', display: 'inline-flex' }}>
                              <Icon name="lock" size={14} />
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {editing && schema && (
          <EditDrawer
            schema={schema}
            initial={editing}
            ownCatalogs={ownCatalogs}
            onClose={() => setEditing(null)}
            onSave={save}
          />
        )}

        {newCatalog && (
          <CatalogDrawer onClose={() => setNewCatalog(false)} onSave={createCatalog} />
        )}
      </div>
    </>
  )
}

function MarketplaceView({ market, ownCatalogs, countsLabel, canManage, canSubscribe, onToggle, onRemoveCatalog }) {
  if (market === null) return <Spinner label="Cargando marketplace…" />
  return (
    <>
      <div className="sun-divider">Tus catálogos · {ownCatalogs.length}</div>
      {ownCatalogs.length === 0 ? (
        <div className="sun-inline-note sun-inline-note--info" style={{ marginBottom: 'var(--space-5)' }}>
          <Icon name="info" size={14} /> Aún no tienes catálogos propios. Crea uno para guardar tus equipos, o se creará «Mis equipos» automáticamente al añadir el primero.
        </div>
      ) : (
        <div className="catalog-grid" style={{ marginBottom: 'var(--space-6)' }}>
          {ownCatalogs.map((c) => (
            <div className="sun-card catalog-card" key={c.id}>
              <div className="catalog-card__head">
                <Icon name="folder" size={18} color="var(--green-600)" />
                <span className="catalog-card__title">{c.nombre}</span>
                {canManage && <IconBtn icon="trash-2" label="Eliminar catálogo" size="sm" onClick={() => onRemoveCatalog(c)} />}
              </div>
              <div className="catalog-card__desc">{c.descripcion || 'Catálogo propio del workspace'}</div>
              <div className="catalog-card__meta">{countsLabel(c)}</div>
            </div>
          ))}
        </div>
      )}

      <div className="sun-divider">Marketplace · {market.length}</div>
      <div className="catalog-grid">
        {market.map((c) => (
          <div className="sun-card catalog-card" key={c.id}>
            <div className="catalog-card__head">
              <Icon name="store" size={18} color="var(--blue-500)" />
              <span className="catalog-card__title">{c.nombre}</span>
              {c.is_official && <Badge tone="info" icon="badge-check">Oficial</Badge>}
            </div>
            <div className="catalog-card__desc">{c.descripcion}</div>
            <div className="catalog-card__meta">{countsLabel(c)}</div>
            <div className="catalog-card__foot">
              {c.subscribed ? (
                <Btn variant="secondary" size="sm" icon="check" disabled={!canSubscribe} onClick={() => onToggle(c)}>En tu biblioteca · Quitar</Btn>
              ) : (
                <Btn variant="primary" size="sm" icon="plus" disabled={!canSubscribe} onClick={() => onToggle(c)}>Añadir a mi biblioteca</Btn>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function EditDrawer({ schema, initial, ownCatalogs, onClose, onSave }) {
  const movable = !initial.id || initial.deletable
  const [values, setValues] = useState(() => {
    const v = {}
    schema.fields.forEach((f) => {
      v[f.key] = initial[f.key] ?? (f.select ? f.select[0] : '')
    })
    v.catalog_id = initial.catalog_id || (ownCatalogs[0]?.id ?? '')
    return v
  })
  const set = (k) => (e) => setValues((s) => ({ ...s, [k]: e.target.value }))

  return (
    <Scrim onClose={onClose} label={`${initial.id ? 'Editar' : 'Nuevo'} ${schema.singular}`}>
      <div className="sun-drawer">
        <div className="sun-drawer__head">
          <h3>{initial.id ? 'Editar' : 'Nuevo'} {schema.singular}</h3>
          <IconBtn icon="x" label="Cerrar" onClick={onClose} />
        </div>
        <div className="sun-drawer__body">
          {!movable ? (
            <div className="sun-inline-note sun-inline-note--info">
              <Icon name="info" size={14} /> Editas el catálogo oficial «{initial.catalog_nombre}». Los cambios afectan a todas las organizaciones y quitan la marca «Scraped».
            </div>
          ) : ownCatalogs.length > 0 ? (
            <SelectField label="Catálogo" value={values.catalog_id} onChange={set('catalog_id')}
              options={ownCatalogs.map((c) => ({ value: c.id, label: c.nombre }))} />
          ) : (
            <div className="sun-inline-note sun-inline-note--info">
              <Icon name="info" size={14} /> Se guardará en tu catálogo «Mis equipos» (se creará automáticamente).
            </div>
          )}
          <div className="sun-speclist">
            {schema.fields.map((f) => (
              f.select ? (
                <SelectField key={f.key} label={f.label} options={f.select} value={values[f.key]} onChange={set(f.key)} />
              ) : (
                <Field
                  key={f.key}
                  label={f.label}
                  required={f.required}
                  numeric={f.num}
                  type={f.num ? 'number' : 'text'}
                  step={f.num ? 'any' : undefined}
                  placeholder={f.placeholder}
                  value={values[f.key]}
                  onChange={set(f.key)}
                />
              )
            ))}
          </div>
        </div>
        <div className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="check" onClick={() => onSave(values)}>Guardar</Btn>
        </div>
      </div>
    </Scrim>
  )
}

function CatalogDrawer({ onClose, onSave }) {
  const [values, setValues] = useState({ nombre: '', descripcion: '' })
  const set = (k) => (e) => setValues((s) => ({ ...s, [k]: e.target.value }))
  return (
    <Scrim onClose={onClose} label="Nuevo catálogo">
      <div className="sun-drawer">
        <div className="sun-drawer__head">
          <h3>Nuevo catálogo</h3>
          <IconBtn icon="x" label="Cerrar" onClick={onClose} />
        </div>
        <div className="sun-drawer__body">
          <Field label="Nombre" required placeholder="Ej: Mis paneles premium" value={values.nombre} onChange={set('nombre')} />
          <Field label="Descripción" placeholder="Equipos que usamos en instalaciones residenciales" value={values.descripcion} onChange={set('descripcion')} />
        </div>
        <div className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="check" onClick={() => onSave(values)}>Crear catálogo</Btn>
        </div>
      </div>
    </Scrim>
  )
}

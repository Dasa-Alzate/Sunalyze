import { useEffect, useId, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Topbar } from '@/shared/ui'
import { Btn, Icon, Field, SelectField, ExportMenu, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { dec, int, num } from '@/shared/format'
import { exportRows } from '@/services/export'
import { toast } from '@/services/toast'
import { GeoMap } from '@/services/geo-map'
import { useAuth } from '@/services/auth'

const STEPS = [
  { title: 'Datos del lugar', icon: 'map-pin' },
  { title: 'Equipos', icon: 'package' },
  { title: 'Análisis', icon: 'bar-chart-3' },
  { title: 'Memoria', icon: 'file-text' },
]

const EMPTY_FORM = {
  cliente: '', localidad: '', direccion: '',
  necesidad: '', autoconsumo: 90,
  latitud: '', longitud: '',
  coplanar: false, inclinacion: '', azimut: '',
}

export default function Wizard() {
  const { id } = useParams()
  const nav = useNavigate()
  const { flag } = useAuth()

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [panels, setPanels] = useState([])
  const [inverters, setInverters] = useState([])
  const [batteries, setBatteries] = useState([])

  const [projectId, setProjectId] = useState(id ? Number(id) : null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [panelId, setPanelId] = useState(null)
  const [inverterId, setInverterId] = useState(null)
  const [batteryId, setBatteryId] = useState(null)
  const [batteryQty, setBatteryQty] = useState(1)

  const [step, setStep] = useState(0)
  const [results, setResults] = useState(null)
  const [stale, setStale] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const [showAll, setShowAll] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    setLoadError(null)
    Promise.all([api.panels.list(), api.inverters.list(), api.batteries.list(), id ? api.projects.get(Number(id)) : Promise.resolve(null)])
      .then(([ps, invs, bats, proj]) => {
        if (!alive) return
        setPanels(ps)
        setInverters(invs)
        setBatteries(bats)
        if (proj) {
          setProjectId(proj.id)
          setForm({
            cliente: proj.cliente || '', localidad: proj.localidad || '', direccion: proj.direccion || '',
            necesidad: proj.necesidad ?? '', autoconsumo: proj.autoconsumo ?? 90,
            latitud: proj.latitud ?? '', longitud: proj.longitud ?? '',
            coplanar: !!proj.coplanar, inclinacion: proj.inclinacion ?? '', azimut: proj.azimut ?? '',
          })
          setPanelId(proj.panel_id || null)
          setInverterId(proj.inverter_id || null)
          setBatteryId(proj.battery_id || null)
          setBatteryQty(proj.battery_quantity ?? 1)
          if (proj.resultados) setResults(proj.resultados)
        }
      })
      .catch((e) => alive && setLoadError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [id])

  const panel = useMemo(() => panels.find((p) => p.id === panelId) || null, [panels, panelId])
  const inverter = useMemo(() => inverters.find((i) => i.id === inverterId) || null, [inverters, inverterId])
  const battery = useMemo(() => batteries.find((b) => b.id === batteryId) || null, [batteries, batteryId])

  function patch(p) { setForm((f) => ({ ...f, ...p })); if (results) setStale(true) }
  function pickPanel(p) { setPanelId(p.id); if (results) setStale(true) }
  function pickInverter(i) { setInverterId(i.id); if (results) setStale(true) }
  function pickBattery(b) { setBatteryId(b.id); if (results) setStale(true) }

  async function analyze() {
    if (!panelId) { toast('warning', 'Selecciona un panel', 'El panel es obligatorio para dimensionar'); setStep(1); return }
    if (!form.latitud || !form.longitud || !form.necesidad) {
      toast('warning', 'Faltan datos del lugar', 'Latitud, longitud y necesidad anual son obligatorias'); setStep(0); return
    }
    setAnalyzing(true)
    setAnalysisError(null)
    const body = {
      panel_id: panelId,
      latitud: Number(form.latitud),
      longitud: Number(form.longitud),
      autoconsumo: Number(form.autoconsumo),
      necesidad: Number(form.necesidad),
      coplanar: !!form.coplanar,
      show_all_inverters: showAll,
    }
    if (inverterId) body.inverter_id = inverterId
    if (batteryId) { body.battery_id = batteryId; body.battery_quantity = Number(batteryQty) || 1 }
    if (form.coplanar) { body.inclinacion = Number(form.inclinacion); body.azimut = Number(form.azimut) }
    try {
      const res = await api.analyze(body)
      setResults(res)
      setStale(false)
      toast('success', 'Dimensionamiento calculado')
    } catch (e) {
      setAnalysisError(e.message)
      toast('error', 'No se pudo calcular', e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  async function save({ estado, silent } = {}) {
    if (!form.cliente.trim()) { toast('warning', 'Pon un nombre de cliente', 'Identifica el proyecto en el paso «Datos del lugar»'); setStep(0); return null }
    setSaving(true)
    const body = {
      cliente: form.cliente.trim(),
      localidad: form.localidad || null,
      direccion: form.direccion || null,
      necesidad: form.necesidad === '' ? null : Number(form.necesidad),
      autoconsumo: Number(form.autoconsumo),
      latitud: form.latitud === '' ? null : Number(form.latitud),
      longitud: form.longitud === '' ? null : Number(form.longitud),
      coplanar: !!form.coplanar,
      inclinacion: form.inclinacion === '' ? null : Number(form.inclinacion),
      azimut: form.azimut === '' ? null : Number(form.azimut),
      panel_id: panelId,
      inverter_id: inverterId,
      battery_id: batteryId,
      battery_quantity: batteryId ? (Number(batteryQty) || 1) : null,
      resultados: results,
    }
    if (estado) body.estado = estado
    else if (results) body.estado = 'diseno'
    try {
      let proj
      if (projectId) {
        proj = await api.projects.update(projectId, body)
      } else {
        proj = await api.projects.create(body)
        setProjectId(proj.id)
        window.history.replaceState(null, '', `/app/diseno/${proj.id}`)
      }
      if (!silent) toast('success', 'Proyecto guardado')
      return proj
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
      return null
    } finally {
      setSaving(false)
    }
  }

  async function goToMemoria() {
    const proj = await save({ silent: true })
    if (proj) nav(`/app/memoria/${proj.id}`)
  }

  async function goToDiagrama() {
    const proj = await save({ silent: true })
    if (proj) nav(`/app/diagrama/${proj.id}`)
  }

  const summary = useMemo(() => buildSummary(results, panel, stale), [results, panel, stale])

  function exportSummary(fmt) {
    const name = `resumen-${(form.cliente || 'proyecto').replace(/\s+/g, '-')}`
    exportRows(fmt, name, ['Métrica', 'Valor', 'Unidad'], summary.map((r) => [r.label, r.value, r.unit || '']))
  }

  const stepState = (i) => {
    if (i === step) return 'active'
    if (stale && i >= 2) return 'stale'
    if (i < step) return 'done'
    return 'pending'
  }

  if (loading) {
    return (<><Topbar title="Diseño" crumb="Proyectos" /><div className="sun-content"><Spinner label="Cargando…" /></div></>)
  }
  if (loadError) {
    return (<><Topbar title="Diseño" crumb="Proyectos" /><div className="sun-content"><ErrorState message={loadError} onRetry={() => nav(0)} /></div></>)
  }

  return (
    <>
      <Topbar
        title={form.cliente || 'Nuevo diseño'}
        crumb="Proyectos"
        actions={
          <>
            <Btn variant="secondary" icon="save" data-busy={saving} disabled={saving} onClick={() => save()}>Guardar</Btn>
            <Btn variant="secondary" icon="workflow" onClick={goToDiagrama}>Diagrama unifilar</Btn>
            <Btn variant="primary" icon="file-text" onClick={goToMemoria}>Ir a la memoria</Btn>
          </>
        }
      />
      <div className="sun-content">
        <div className="sun-wizard">
          <nav className="sun-stepper">
            {STEPS.map((s, i) => {
              const st = stepState(i)
              return (
                <button key={i} className={`sun-step sun-step--${st}`} onClick={() => setStep(i)}>
                  <span className="sun-step__marker">
                    {st === 'done' ? <Icon name="check" size={15} /> : st === 'stale' ? <Icon name="alert-triangle" size={15} /> : (i + 1)}
                  </span>
                  <span className="sun-step__body">
                    <span className="sun-step__idx">Paso {i + 1}</span>
                    <span className="sun-step__title">{s.title}</span>
                  </span>
                </button>
              )
            })}
          </nav>

          <div className="sun-wizard__panel sun-wizard__pad">
            {step === 0 && (
              <>
                <div className="sun-divider">Cliente</div>
                <div className="sun-wizard__formgrid">
                  <Field label="Cliente / proyecto" required value={form.cliente} onChange={(e) => patch({ cliente: e.target.value })} placeholder="Ej: J. García" />
                  <Field label="Localidad" value={form.localidad} onChange={(e) => patch({ localidad: e.target.value })} placeholder="Alicante" />
                </div>
                <Field label="Dirección" value={form.direccion} onChange={(e) => patch({ direccion: e.target.value })} placeholder="C/ Mayor 4, 2ºA" />

                <div className="sun-divider">Emplazamiento y consumo</div>
                <div className="sun-wizard__formgrid">
                  <Field label="Necesidad anual" numeric type="number" step="any" value={form.necesidad} onChange={(e) => patch({ necesidad: e.target.value })} hint="kWh/año" required />
                  <SelectField label="Autoconsumo" value={form.autoconsumo} onChange={(e) => patch({ autoconsumo: e.target.value })}
                    options={[{ value: 70, label: '70 %' }, { value: 80, label: '80 %' }, { value: 90, label: '90 %' }, { value: 100, label: '100 %' }]} />
                  <Field label="Latitud" numeric type="number" step="any" value={form.latitud} onChange={(e) => patch({ latitud: e.target.value })} placeholder="38.352" required />
                  <Field label="Longitud" numeric type="number" step="any" value={form.longitud} onChange={(e) => patch({ longitud: e.target.value })} placeholder="-0.493" required />
                </div>
                {flag('geo_map') && (
                  <div style={{ marginTop: 'var(--space-4)' }}>
                    <GeoMap
                      lat={form.latitud}
                      lon={form.longitud}
                      onPick={(la, lo, name) => patch({ latitud: la, longitud: lo, localidad: form.localidad || (name ? name.split(',')[0] : form.localidad) })}
                    />
                  </div>
                )}
                <label className="sun-check" style={{ marginTop: 'var(--space-4)' }}>
                  <input type="checkbox" checked={form.coplanar} onChange={(e) => patch({ coplanar: e.target.checked })} />
                  <span className="sun-check__box"><Icon name="check" size={13} /></span>
                  <span>Instalación coplanar (definir inclinación y azimut)</span>
                </label>
                {form.coplanar && (
                  <div className="sun-wizard__formgrid" style={{ marginTop: 'var(--space-4)' }}>
                    <Field label="Inclinación (°)" numeric type="number" step="any" value={form.inclinacion} onChange={(e) => patch({ inclinacion: e.target.value })} />
                    <Field label="Azimut (°)" numeric type="number" step="any" value={form.azimut} onChange={(e) => patch({ azimut: e.target.value })} hint="180 = sur" />
                  </div>
                )}
              </>
            )}

            {step === 1 && (
              <>
                <div className="sun-divider">Selección de equipos</div>
                <div className="sun-field" style={{ marginBottom: 'var(--space-4)' }}>
                  <span className="sun-field__label" id="ss-panel">Panel solar <span className="req">*</span></span>
                  <SearchSelect labelId="ss-panel" placeholder="Buscar panel (nombre, potencia…)" options={panels} value={panel} onPick={pickPanel} meta={panelMeta} />
                </div>
                <div className="sun-field">
                  <span className="sun-field__label" id="ss-inverter">
                    Inversor <span style={{ color: 'var(--text-subtle)', fontWeight: 500 }}>· opcional — déjalo vacío para ver compatibles</span>
                  </span>
                  <SearchSelect labelId="ss-inverter" placeholder="Buscar inversor…" options={inverters} value={inverter} onPick={pickInverter} meta={inverterMeta} clearable onClear={() => { setInverterId(null); if (results) setStale(true) }} />
                </div>
                <div className="sun-field" style={{ marginTop: 'var(--space-4)' }}>
                  <span className="sun-field__label" id="ss-battery">
                    Batería <span style={{ color: 'var(--text-subtle)', fontWeight: 500 }}>· opcional — déjala vacía para «Sin batería»</span>
                  </span>
                  <SearchSelect labelId="ss-battery" placeholder="Buscar batería…" options={batteries} value={battery} onPick={pickBattery} meta={batteryMeta} clearable onClear={() => { setBatteryId(null); if (results) setStale(true) }} />
                </div>
                {battery && (
                  <div style={{ marginTop: 'var(--space-4)', maxWidth: 220 }}>
                    <Field label="Cantidad de baterías" numeric type="number" step="1" min="1" value={batteryQty}
                      onChange={(e) => { setBatteryQty(e.target.value); if (results) setStale(true) }} hint="ud" />
                  </div>
                )}
                <label className="sun-check" style={{ marginTop: 'var(--space-4)' }}>
                  <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />
                  <span className="sun-check__box"><Icon name="check" size={13} /></span>
                  <span>Mostrar todos los inversores compatibles (desactivar filtro por potencia)</span>
                </label>
              </>
            )}

            {step === 2 && (
              <>
                <div className="sun-divider">Resultados del dimensionamiento</div>
                {analysisError && <div className="sun-inline-note sun-inline-note--danger" style={{ marginBottom: 'var(--space-4)' }}><Icon name="alert-triangle" size={14} />{analysisError}</div>}
                {!results ? (
                  <div className="sun-empty" style={{ border: 0, padding: 'var(--space-8) 0' }}>
                    <div className="sun-empty__icon"><Icon name="bar-chart-3" size={26} /></div>
                    <div className="sun-empty__title">Sin cálculo todavía</div>
                    <div className="sun-empty__desc">Calcula el dimensionamiento con los datos del lugar y el panel seleccionado. Los datos de irradiancia provienen de PVGIS.</div>
                    <div className="sun-empty__actions"><Btn variant="primary" icon="play" data-busy={analyzing} disabled={analyzing} onClick={analyze}>{analyzing ? 'Calculando…' : 'Calcular dimensionamiento'}</Btn></div>
                  </div>
                ) : (
                  <>
                    <div className="sun-resultgrid">
                      {buildResultCards(results, panel).map((m) => (
                        <div key={m.label} className="sun-kpi" style={{ boxShadow: 'none' }}>
                          <span className="sun-metric__label">{m.label}</span>
                          <span className="sun-metric__value">{m.value}<span className="unit">{m.unit}</span></span>
                        </div>
                      ))}
                    </div>
                    {!inverter && results.compatible_inverters && (
                      <CompatibleInverters list={results.compatible_inverters} onPick={(inv) => { pickInverter(inv); toast('info', 'Inversor seleccionado', 'Recalcula para el dimensionamiento completo') }} />
                    )}
                    {results.battery && <BatteryResult battery={results.battery} />}
                    <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                      <Btn variant="secondary" icon="refresh-cw" data-busy={analyzing} disabled={analyzing} onClick={analyze}>{analyzing ? 'Recalculando…' : 'Recalcular'}</Btn>
                      <span style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                        <Icon name="info" size={15} color="var(--info)" /> Datos de irradiancia: PVGIS-SARAH3.
                      </span>
                    </div>
                  </>
                )}
              </>
            )}

            {step === 3 && (
              <div className="sun-empty" style={{ border: 0, padding: 'var(--space-8) 0' }}>
                <div className="sun-empty__icon"><Icon name="file-text" size={26} /></div>
                <div className="sun-empty__title">Listo para la memoria técnica</div>
                <div className="sun-empty__desc">Completa los datos del cliente y la instalación; verás el documento crecer en vivo.</div>
                <div className="sun-empty__actions"><Btn variant="primary" icon="arrow-right" onClick={goToMemoria}>Ir a la memoria</Btn></div>
              </div>
            )}

            <div className="sun-wizard__nav">
              <Btn variant="secondary" icon="arrow-left" disabled={step === 0} onClick={() => setStep(Math.max(0, step - 1))}>Atrás</Btn>
              {step === 1 ? (
                <Btn variant="primary" iconRight="arrow-right" data-busy={analyzing} disabled={analyzing} onClick={() => { setStep(2); if (!results || stale) analyze() }}>{analyzing ? 'Calculando…' : 'Calcular y continuar'}</Btn>
              ) : (
                <Btn variant="primary" iconRight="arrow-right" onClick={() => (step < 3 ? setStep(step + 1) : goToMemoria())}>{step < 3 ? 'Continuar' : 'Generar memoria'}</Btn>
              )}
            </div>
          </div>

          <div className="sun-wizard__panel sun-wizard__summary">
            <div className="sun-summary-head">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><Icon name="activity" size={14} /> Resumen vivo</span>
              <ExportMenu iconOnly align="right" onExport={exportSummary} />
            </div>
            <div className="sun-summary-list">
              {summary.map((r) => (
                <div key={r.label} className={`sun-summary-row${r.stale ? ' sun-summary-row--stale' : ''}`}>
                  <span className="sun-summary-row__k">{r.label}{r.stale && <Icon name="alert-triangle" size={12} color="var(--state-warn)" style={{ marginLeft: 6 }} />}</span>
                  <span className="sun-summary-row__v">{r.value}{r.unit && <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 3 }}>{r.unit}</span>}</span>
                </div>
              ))}
            </div>
            {stale && (
              <div style={{ padding: 'var(--space-3) var(--space-5)', borderTop: '1px solid var(--border-subtle)' }}>
                <div className="sun-inline-note"><Icon name="alert-triangle" size={14} /> Entradas cambiadas — recalcula para actualizar</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

function panelMeta(p) {
  return `${dec(p.power)} W · Voc ${dec(p.voc)} V`
}
function inverterMeta(i) {
  return `${dec(i.power)} kW · Vmax ${int(i.vmax)} V`
}
function batteryMeta(b) {
  return `${dec(b.capacity_kwh)} kWh · ${dec(b.power_kw)} kW${b.technology ? ` · ${b.technology}` : ''}`
}

function SearchSelect({ placeholder, options, value, onPick, meta, clearable, onClear, labelId }) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const listId = useId()
  const list = q ? options.filter((o) => o.nombre.toLowerCase().includes(q.toLowerCase())) : options
  return (
    <div className="sun-search" onMouseLeave={() => setOpen(false)}>
      <div className="sun-search__control">
        <Icon name="search" size={16} />
        <input
          className="sun-search__input"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-labelledby={labelId}
          placeholder={value ? value.nombre : placeholder}
          value={q}
          onFocus={() => setOpen(true)}
          onChange={(e) => { setQ(e.target.value); setOpen(true) }}
        />
        {value && clearable && (
          <button type="button" className="sun-search__clear" aria-label="Borrar selección" onClick={(e) => { e.stopPropagation(); onClear && onClear() }}>
            <Icon name="x" size={16} color="var(--text-subtle)" />
          </button>
        )}
        {value && !clearable && <Icon name="check" size={16} color="var(--state-valid)" />}
      </div>
      {open && (
        <div className="sun-search__menu" role="listbox" id={listId}>
          {list.length === 0 && <div className="sun-search__empty">Sin coincidencias</div>}
          {list.map((o) => (
            <button
              type="button"
              key={o.id}
              role="option"
              aria-selected={value && value.id === o.id}
              className={`sun-search__opt${value && value.id === o.id ? ' sun-search__opt--active' : ''}`}
              onClick={() => { onPick(o); setOpen(false); setQ('') }}
            >
              <span className="sun-search__opt-name">{o.nombre}</span>
              <span className="sun-search__opt-meta">{meta(o)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function CompatibleInverters({ list, onPick }) {
  return (
    <div style={{ marginTop: 'var(--space-5)' }}>
      <div className="sun-divider">Inversores compatibles · {list.length}</div>
      {list.length === 0 ? (
        <div className="sun-inline-note"><Icon name="alert-triangle" size={14} /> Ningún inversor de la biblioteca cumple los criterios. Revisa el campo o añade inversores.</div>
      ) : (
        <table className="sun-table">
          <thead><tr><th>Inversor</th><th style={{ textAlign: 'right' }}>kW</th><th style={{ textAlign: 'right' }}>Vmax</th><th style={{ textAlign: 'right' }}>Margen V</th><th></th></tr></thead>
          <tbody>
            {list.map((inv) => (
              <tr key={inv.id}>
                <td className="sun-table__name">{inv.nombre}</td>
                <td className="num" style={{ textAlign: 'right' }}>{dec(inv.power)}</td>
                <td className="num" style={{ textAlign: 'right' }}>{int(inv.vmax)}</td>
                <td className="num" style={{ textAlign: 'right' }}>{dec(inv.compatibility_margin)} %</td>
                <td style={{ textAlign: 'right' }}><Btn variant="ghost" size="sm" onClick={() => onPick(inv)}>Elegir</Btn></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function BatteryResult({ battery }) {
  const cards = [
    { label: 'Banco útil', value: dec(battery.bank_usable_kwh), unit: 'kWh' },
    { label: 'Banco nominal', value: dec(battery.bank_capacity_kwh), unit: 'kWh' },
    { label: 'Útil recomendado', value: dec(battery.recommended_usable_kwh), unit: 'kWh' },
    { label: 'Autoconsumo estimado', value: dec(battery.estimated_self_consumption_pct), unit: '%' },
    { label: 'Aporte anual batería', value: int(battery.annual_battery_contribution_kwh), unit: 'kWh' },
  ]
  return (
    <div style={{ marginTop: 'var(--space-5)' }}>
      <div className="sun-divider">Batería · {battery.nombre}{battery.quantity > 1 ? ` ×${battery.quantity}` : ''}</div>
      <div className="sun-resultgrid">
        {cards.map((m) => (
          <div key={m.label} className="sun-kpi" style={{ boxShadow: 'none' }}>
            <span className="sun-metric__label">{m.label}</span>
            <span className="sun-metric__value">{m.value}<span className="unit">{m.unit}</span></span>
          </div>
        ))}
      </div>
      {battery.method_note && (
        <div className="sun-inline-note" style={{ marginTop: 'var(--space-4)' }}>
          <Icon name="info" size={14} color="var(--info)" />{battery.method_note}
        </div>
      )}
    </div>
  )
}

function panelesFrom(results, panel) {
  if (results?.cell_amount != null) return Math.ceil(Number(results.cell_amount))
  if (results?.total_field_power != null && panel?.power) return Math.round((Number(results.total_field_power) * 1000) / Number(panel.power))
  return null
}

function buildSummary(results, panel, stale) {
  if (!results) {
    return [
      { label: 'Irradiancia', value: '—' },
      { label: 'Ángulo óptimo', value: '—' },
      { label: 'Campo FV', value: '—' },
      { label: 'Paneles', value: '—' },
      { label: 'Producción anual', value: '—' },
    ]
  }
  const irr = results.optimal_irradiance ?? results.annual_irradiance_kWh_m2
  const np = panelesFrom(results, panel)
  return [
    { label: 'Irradiancia', value: irr != null ? int(irr) : '—', unit: 'kWh/m²', stale },
    { label: 'Ángulo óptimo', value: results.beta_optimal != null ? `${Math.round(results.beta_optimal)}°` : '—', stale },
    { label: 'Campo FV', value: results.total_field_power != null ? dec(results.total_field_power) : '—', unit: 'kWp', stale },
    { label: 'Paneles', value: np != null ? np : '—', unit: 'ud', stale },
    { label: 'Producción anual', value: results.annual_production != null ? int(results.annual_production) : '—', unit: 'kWh', stale },
  ]
}

function buildResultCards(results, panel) {
  const np = panelesFrom(results, panel)
  const cards = [
    { label: 'Potencia pico de campo', value: results.total_field_power != null ? dec(results.total_field_power) : '—', unit: 'kWp' },
    { label: 'Producción anual estimada', value: results.annual_production != null ? int(results.annual_production) : '—', unit: 'kWh' },
    { label: 'Paneles', value: np != null ? np : '—', unit: 'ud' },
  ]
  if (results.cell_area != null) cards.push({ label: 'Superficie necesaria', value: dec(results.cell_area), unit: 'm²' })
  if (results.total_y != null && panel?.y) cards.push({ label: 'Rendimiento (PR)', value: num((Number(results.total_y) / (Number(panel.y) / 100)) * 100, 1), unit: '%' })
  if (results.max_cell_amount != null) cards.push({ label: 'Paneles máx. por cadena', value: Math.floor(Number(results.max_cell_amount)), unit: 'ud' })
  if (results.annual_irradiance_kWh_m2 != null) cards.push({ label: 'Irradiancia anual', value: int(results.annual_irradiance_kWh_m2), unit: 'kWh/m²' })
  return cards
}

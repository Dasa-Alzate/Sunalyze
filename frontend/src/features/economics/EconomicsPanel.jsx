import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Btn, Icon, SelectField, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { SweepChart, PaybackChart, MonthlyBillChart, MonthlyBillTable, DayTypeChart } from './charts'
import './economics.css'

const eur = (v) => `${v.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`

const TABS = [
  { key: 'factura', label: 'Factura mensual', icon: 'receipt' },
  { key: 'diatipo', label: 'Día tipo', icon: 'sun' },
]

export function EconomicsPanel({ projectId, profileId, planId, onPlanChange, onSave }) {
  const [data, setData] = useState(null)
  const [sweep, setSweep] = useState(null)
  const [scenarios, setScenarios] = useState(null)
  const [plans, setPlans] = useState([])
  const [busy, setBusy] = useState(false)
  const [batteryBusy, setBatteryBusy] = useState(false)
  const [tab, setTab] = useState('factura')

  useEffect(() => {
    let alive = true
    api.electricityPlans.list()
      .then((list) => { if (alive) setPlans(list || []) })
      .catch(() => { if (alive) setPlans([]) })
    return () => { alive = false }
  }, [])

  async function loadBatteryOptions() {
    setBatteryBusy(true)
    try {
      const [sw, sc] = await Promise.all([
        api.economics.sweep(projectId),
        api.economics.scenarios(projectId),
      ])
      setSweep(sw)
      setScenarios(sc)
    } catch (err) {
      toast('error', 'No se pudieron comparar las baterías', err.data?.error || err.message)
    } finally {
      setBatteryBusy(false)
    }
  }

  async function compute() {
    setBusy(true)
    try {
      if (onSave && await onSave() === null) { setBusy(false); return }
      setData(await api.economics.compute(projectId))
      setSweep(null)
      setScenarios(null)
      loadBatteryOptions()
    } catch (err) {
      toast('error', 'No se pudo calcular el ahorro', err.data?.error || err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!profileId) {
    return (
      <div className="eco-panel eco-panel--empty">
        <Icon name="piggy-bank" size={16} />
        <span>Asocia un <strong>perfil de consumo</strong> en el paso «Datos del lugar» para calcular la factura y el aporte real de la batería.</span>
      </div>
    )
  }
  if (!projectId) {
    return (
      <div className="eco-panel eco-panel--empty">
        <Icon name="piggy-bank" size={16} />
        <span>Guarda el proyecto para calcular el ahorro económico.</span>
      </div>
    )
  }

  const conBateria = data?.bateria
  const facturaFinal = conBateria ? conBateria.factura : data?.factura_fv
  const planOptions = [
    { value: '', label: 'Tarifa de referencia de la organización (2.0TD)' },
    ...plans.map((p) => ({ value: p.id, label: `${p.comercializadora} · ${p.nombre}` })),
  ]

  return (
    <>
      <div className="eco-panel">
        <div className="eco-panel__head">
          <h4><Icon name="piggy-bank" size={16} /> Ahorro económico{data ? ` · ${data.tarifa.nombre}` : ''}</h4>
          <Btn variant={data ? 'secondary' : 'primary'} icon="calculator" data-busy={busy} disabled={busy} onClick={compute}>
            {busy ? 'Calculando…' : data ? 'Recalcular' : 'Calcular ahorro'}
          </Btn>
        </div>
        <div className="eco-plan">
          <SelectField label="Plan eléctrico del cliente" value={planId ?? ''} options={planOptions}
            onChange={(e) => onPlanChange(e.target.value === '' ? null : Number(e.target.value))} />
          <span className="eco-plan__hint">
            Los planes se crean y editan en <Link to="/app/equipos?tab=planes">Equipos › Planes eléctricos</Link>. Recalcula tras cambiarlo.
          </span>
        </div>
        {busy && !data && <Spinner label="Cruzando consumo y producción hora a hora…" />}
        {data && (
          <>
            <div className="eco-grid">
              <div className="eco-kpi">
                <span className="eco-kpi__label">Factura sin placas</span>
                <span className="eco-kpi__value">{eur(data.factura_base.total)}<span className="unit">/año</span></span>
              </div>
              <div className="eco-kpi">
                <span className="eco-kpi__label">{conBateria ? 'Factura con FV + batería' : 'Factura con FV'}</span>
                <span className="eco-kpi__value">{eur(facturaFinal.total)}<span className="unit">/año</span></span>
              </div>
              <div className="eco-kpi eco-kpi--good">
                <span className="eco-kpi__label">Ahorro anual</span>
                <span className="eco-kpi__value">{eur(data.ahorro_total)}<span className="unit">/año</span></span>
              </div>
              <div className="eco-kpi">
                <span className="eco-kpi__label">Autoconsumo real</span>
                <span className="eco-kpi__value">
                  {(conBateria ? conBateria.autoconsumo_total_pct : data.autoconsumo_directo_pct).toLocaleString('es-ES')}
                  <span className="unit">%</span>
                </span>
              </div>
              {conBateria && (
                <div className="eco-kpi">
                  <span className="eco-kpi__label">Aporte de la batería</span>
                  <span className="eco-kpi__value">{eur(conBateria.ahorro_bateria)}<span className="unit">/año</span></span>
                </div>
              )}
            </div>
            {facturaFinal.hucha_perdida > 0 && (
              <p className="eco-panel__note">
                <Icon name="info" size={13} /> {eur(facturaFinal.hucha_perdida)} de excedentes no llegan a descontarse
                (la compensación no supera la factura): margen para más batería o menos campo.
              </p>
            )}
            <div className="eco-tabs" role="tablist">
              {TABS.map((t) => (
                <button key={t.key} type="button" role="tab" aria-selected={tab === t.key}
                  className={`eco-tab${tab === t.key ? ' eco-tab--active' : ''}`}
                  onClick={() => setTab(t.key)}>
                  <Icon name={t.icon} size={13} />{t.label}
                </button>
              ))}
            </div>
            <div className="eco-tabbody">
              {tab === 'factura' && (
                <>
                  <MonthlyBillChart antes={data.factura_base.meses} despues={facturaFinal.meses} />
                  <MonthlyBillTable antes={data.factura_base.meses} despues={facturaFinal.meses}
                    totalAntes={data.factura_base.total} totalDespues={facturaFinal.total} />
                </>
              )}
              {tab === 'diatipo' && <DayTypeChart diaTipo={data.dia_tipo} />}
            </div>
          </>
        )}
      </div>

      {data && (
        <div className="eco-panel">
          <div className="eco-panel__head">
            <h4><Icon name="battery-charging" size={16} /> Selección de batería</h4>
            <Btn variant="secondary" icon="refresh-cw" data-busy={batteryBusy} disabled={batteryBusy} onClick={loadBatteryOptions}>
              {batteryBusy ? 'Simulando…' : 'Volver a comparar'}
            </Btn>
          </div>
          {batteryBusy && !sweep && <Spinner label="Simulando escenarios de batería…" />}
          {sweep && (
            <div className="eco-section">
              <h5>Potencia fotovoltaica frente a ahorro</h5>
              <SweepChart sweep={sweep} />
            </div>
          )}
          {scenarios && (
            <>
              <div className="eco-section">
                <h5>Payback frente a ahorro</h5>
                <PaybackChart scenarios={scenarios} />
              </div>
              <div className="eco-section">
                <h5>Rentabilidad por batería</h5>
                <table className="sun-table eco-scenarios__table">
                  <thead>
                    <tr>
                      <th>Batería (con el campo actual)</th>
                      <th style={{ textAlign: 'right' }}>kWh</th>
                      <th style={{ textAlign: 'right' }}>Factura/año</th>
                      <th style={{ textAlign: 'right' }}>Ahorro/año</th>
                      <th style={{ textAlign: 'right' }}>Aporte batería</th>
                      <th style={{ textAlign: 'right' }}>Payback batería</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenarios.escenarios.map((row, i) => (
                      <tr key={row.battery_id ?? 'none'}>
                        <td className="eco-scenarios__name">
                          {row.nombre}{' '}
                          {i === 0 && row.battery_id !== null && <Badge tone="success">Mayor ahorro</Badge>}
                        </td>
                        <td style={{ textAlign: 'right' }}>{row.capacity_kwh || '—'}</td>
                        <td style={{ textAlign: 'right' }}>{eur(row.factura_anual)}</td>
                        <td style={{ textAlign: 'right' }}>{eur(row.ahorro_anual)}</td>
                        <td style={{ textAlign: 'right' }}>{row.battery_id ? eur(row.ahorro_bateria) : '—'}</td>
                        <td style={{ textAlign: 'right' }}>
                          {row.payback_bateria_anios != null ? `${row.payback_bateria_anios.toLocaleString('es-ES')} años` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </>
  )
}

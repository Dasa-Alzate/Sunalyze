import { useState } from 'react'
import { Badge, Btn, Icon, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import './economics.css'

const eur = (v) => `${v.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`

export function EconomicsPanel({ projectId, profileId, dirty }) {
  const [data, setData] = useState(null)
  const [scenarios, setScenarios] = useState(null)
  const [busy, setBusy] = useState(false)
  const [comparing, setComparing] = useState(false)

  async function compute() {
    setBusy(true)
    try {
      setData(await api.economics.compute(projectId))
    } catch (err) {
      toast('error', 'No se pudo calcular el ahorro', err.data?.error || err.message)
    } finally {
      setBusy(false)
    }
  }

  async function compare() {
    setComparing(true)
    try {
      setScenarios(await api.economics.scenarios(projectId))
    } catch (err) {
      toast('error', 'No se pudo comparar', err.data?.error || err.message)
    } finally {
      setComparing(false)
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

  return (
    <div className="eco-panel">
      <div className="eco-panel__head">
        <h4><Icon name="piggy-bank" size={16} /> Ahorro económico ({data ? data.tarifa.nombre : '2.0TD'})</h4>
        <div className="eco-panel__actions">
          <Btn variant={data ? 'secondary' : 'primary'} icon="calculator" data-busy={busy} disabled={busy} onClick={compute}>
            {busy ? 'Calculando…' : data ? 'Recalcular' : 'Calcular ahorro'}
          </Btn>
          {data && (
            <Btn variant="secondary" icon="scale" data-busy={comparing} disabled={comparing} onClick={compare}>
              {comparing ? 'Comparando…' : 'Comparar baterías'}
            </Btn>
          )}
        </div>
      </div>
      {dirty && data && (
        <p className="eco-panel__stale"><Icon name="alert-triangle" size={13} /> Hay cambios sin guardar: el cálculo usa la última versión guardada del proyecto.</p>
      )}
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
        </>
      )}
      {scenarios && (
        <div className="eco-scenarios">
          <h5>Comparativa de baterías (mismo campo FV)</h5>
          <table className="sun-table">
            <thead>
              <tr>
                <th>Batería</th>
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
                  <td className="cp-table-name">
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
      )}
    </div>
  )
}

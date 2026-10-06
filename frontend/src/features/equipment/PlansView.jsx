import { useEffect, useState } from 'react'
import { Badge, Btn, ConfirmDialog, Field, Icon, IconBtn, Scrim, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import './plans.css'

export const PLAN_PRICE_FIELDS = [
  { key: 'precio_punta', label: 'Energía punta', unit: '€/kWh', step: '0.0001' },
  { key: 'precio_llano', label: 'Energía llano', unit: '€/kWh', step: '0.0001' },
  { key: 'precio_valle', label: 'Energía valle', unit: '€/kWh', step: '0.0001' },
  { key: 'precio_excedente', label: 'Compensación de excedentes', unit: '€/kWh', step: '0.0001' },
  { key: 'precio_potencia_p1_dia', label: 'Potencia P1', unit: '€/kW·día', step: '0.0001' },
  { key: 'precio_potencia_p2_dia', label: 'Potencia P2', unit: '€/kW·día', step: '0.0001' },
  { key: 'impuesto_electricidad', label: 'Impuesto eléctrico', unit: 'fracción (0,0511 = 5,11 %)', step: '0.0001' },
  { key: 'iva_pct', label: 'IVA', unit: '%', step: '0.1' },
  { key: 'alquiler_contador_mes', label: 'Alquiler de contador', unit: '€/mes', step: '0.01' },
]

const EMPTY_PLAN = {
  comercializadora: '', nombre: '', peaje: '2.0TD',
  precio_punta: 0.193, precio_llano: 0.135, precio_valle: 0.083, precio_excedente: 0.06,
  precio_potencia_p1_dia: 0.077, precio_potencia_p2_dia: 0.0077,
  impuesto_electricidad: 0.0511, iva_pct: 21, alquiler_contador_mes: 0.81,
}

const price = (v) => (v != null ? Number(v).toLocaleString('es-ES', { maximumFractionDigits: 4 }) : '—')

export function PlansView({ canEdit }) {
  const [plans, setPlans] = useState(null)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [saving, setSaving] = useState(false)

  async function load() {
    try {
      setPlans(await api.electricityPlans.list())
    } catch (err) {
      toast('error', 'No se pudieron cargar los planes', err.message)
      setPlans([])
    }
  }

  useEffect(() => { load() }, [])

  function startCreate(base) {
    const source = base ? { ...base, nombre: `${base.nombre} (copia)` } : EMPTY_PLAN
    setEditing({ id: null, form: { ...EMPTY_PLAN, ...source } })
  }

  async function submit(e) {
    e.preventDefault()
    const { id, form } = editing
    const body = { comercializadora: form.comercializadora.trim(), nombre: form.nombre.trim(), peaje: (form.peaje || '2.0TD').trim() }
    for (const f of PLAN_PRICE_FIELDS) body[f.key] = Number(form[f.key])
    if (!body.comercializadora || !body.nombre) return
    setSaving(true)
    try {
      if (id) await api.electricityPlans.update(id, body)
      else await api.electricityPlans.create(body)
      toast('success', id ? 'Plan actualizado' : 'Plan creado')
      setEditing(null)
      load()
    } catch (err) {
      toast('error', 'No se pudo guardar el plan', err.data?.error || err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    try {
      await api.electricityPlans.remove(deleting.id)
      toast('success', 'Plan eliminado')
      setDeleting(null)
      load()
    } catch (err) {
      toast('error', 'No se pudo eliminar', err.data?.error || err.message)
    }
  }

  if (plans === null) return <Spinner label="Cargando planes eléctricos…" />

  const setField = (key, value) => setEditing((cur) => ({ ...cur, form: { ...cur.form, [key]: value } }))

  return (
    <>
      <div className="ep-bar">
        <span className="ep-bar__hint">Los precios de cada plan alimentan la factura y el ahorro del análisis económico de los proyectos que lo usen.</span>
        {canEdit && <Btn variant="primary" icon="plus" onClick={() => startCreate(null)}>Añadir plan</Btn>}
      </div>
      {plans.length === 0 ? (
        <div className="sun-empty" style={{ border: 0, padding: 'var(--space-8) 0' }}>
          <div className="sun-empty__icon"><Icon name="zap" size={26} /></div>
          <div className="sun-empty__title">Sin planes eléctricos</div>
          <div className="sun-empty__desc">Añade los planes de las comercializadoras con las que trabajan tus clientes. Mientras no haya ninguno, el análisis usa la tarifa 2.0TD de referencia de la organización.</div>
        </div>
      ) : (
        <table className="sun-table">
          <thead>
            <tr>
              <th>Comercializadora</th>
              <th>Plan</th>
              <th>Peaje</th>
              <th style={{ textAlign: 'right' }}>Punta</th>
              <th style={{ textAlign: 'right' }}>Llano</th>
              <th style={{ textAlign: 'right' }}>Valle</th>
              <th style={{ textAlign: 'right' }}>Excedente</th>
              <th aria-label="Acciones" />
            </tr>
          </thead>
          <tbody>
            {plans.map((p) => (
              <tr key={p.id}>
                <td className="ep-name">{p.comercializadora}</td>
                <td>{p.nombre} {p.is_global && <Badge tone="info">Global</Badge>}</td>
                <td>{p.peaje}</td>
                <td style={{ textAlign: 'right' }}>{price(p.precio_punta)}</td>
                <td style={{ textAlign: 'right' }}>{price(p.precio_llano)}</td>
                <td style={{ textAlign: 'right' }}>{price(p.precio_valle)}</td>
                <td style={{ textAlign: 'right' }}>{price(p.precio_excedente)}</td>
                <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  {canEdit && (
                    <IconBtn icon="copy" label={`Duplicar ${p.nombre}`} size="sm" onClick={() => startCreate(p)} />
                  )}
                  {canEdit && !p.is_global && (
                    <>
                      <IconBtn icon="pencil" label={`Editar ${p.nombre}`} size="sm"
                        onClick={() => setEditing({ id: p.id, form: { ...EMPTY_PLAN, ...p } })} />
                      <IconBtn icon="trash-2" label={`Eliminar ${p.nombre}`} size="sm" onClick={() => setDeleting(p)} />
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {editing && (
        <Scrim onClose={() => setEditing(null)} label={editing.id ? 'Editar plan eléctrico' : 'Nuevo plan eléctrico'} center>
          <div className="ep-modal">
            <h3><Icon name="zap" size={16} /> {editing.id ? 'Editar plan eléctrico' : 'Nuevo plan eléctrico'}</h3>
            <form onSubmit={submit}>
              <div className="ep-modal__grid">
                <Field label="Comercializadora" required value={editing.form.comercializadora} onChange={(e) => setField('comercializadora', e.target.value)} />
                <Field label="Nombre del plan" required value={editing.form.nombre} onChange={(e) => setField('nombre', e.target.value)} />
                <Field label="Peaje de acceso" value={editing.form.peaje} onChange={(e) => setField('peaje', e.target.value)} />
                {PLAN_PRICE_FIELDS.map((f) => (
                  <Field key={f.key} label={f.label} hint={f.unit} numeric type="number" min="0" step={f.step} required
                    value={editing.form[f.key]} onChange={(e) => setField(f.key, e.target.value)} />
                ))}
              </div>
              <div className="ep-modal__actions">
                <Btn variant="ghost" type="button" onClick={() => setEditing(null)}>Cancelar</Btn>
                <Btn variant="primary" icon="save" type="submit" data-busy={saving} disabled={saving}>Guardar</Btn>
              </div>
            </form>
          </div>
        </Scrim>
      )}
      <ConfirmDialog
        open={Boolean(deleting)}
        title="Eliminar plan eléctrico"
        description={deleting ? `«${deleting.comercializadora} · ${deleting.nombre}» dejará de estar disponible; los proyectos que lo usan pasarán a la tarifa de referencia.` : ''}
        onClose={() => setDeleting(null)}
        actions={[
          { label: 'Cancelar', variant: 'ghost', onClick: () => setDeleting(null) },
          { label: 'Eliminar', variant: 'danger', icon: 'trash-2', onClick: remove },
        ]}
      />
    </>
  )
}

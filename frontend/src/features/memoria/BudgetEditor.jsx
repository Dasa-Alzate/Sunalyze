import { useEffect, useState } from 'react'
import { Btn, IconBtn, Icon, Spinner, ConfirmDialog } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

const CAPITULOS = {
  1: 'Equipos',
  2: 'Instalación eléctrica',
  3: 'Estructura y montaje',
  4: 'Legalización y tramitación',
}

const IVA_OPTS = [21, 10, 4, 0]

function money(v) {
  return (Number(v) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function BudgetEditor({ projectId, canEdit, onSaved }) {
  const [items, setItems] = useState([])
  const [ivaPct, setIvaPct] = useState(21)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [confirmSeed, setConfirmSeed] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    api.projects.budget.get(projectId)
      .then((b) => {
        if (!alive) return
        setItems(b.items)
        setIvaPct(b.iva_pct ?? 21)
      })
      .catch((e) => toast('error', 'No se pudo cargar el presupuesto', e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [projectId])

  const base = items.reduce((sum, i) => sum + (Number(i.cantidad) || 0) * (Number(i.precio_unitario) || 0), 0)
  const iva = base * ivaPct / 100
  const total = base + iva

  function updateItem(idx, patch) {
    setItems((list) => list.map((i, n) => (n === idx ? { ...i, ...patch } : i)))
    setDirty(true)
  }

  function addItem(capitulo) {
    setItems((list) => [...list, { capitulo, descripcion: '', unidad: 'ud', cantidad: 1, precio_unitario: 0 }])
    setDirty(true)
  }

  function removeItem(idx) {
    setItems((list) => list.filter((_, n) => n !== idx))
    setDirty(true)
  }

  function applyResponse(b) {
    setItems(b.items)
    setIvaPct(b.iva_pct ?? 21)
    setDirty(false)
    onSaved && onSaved()
  }

  async function save() {
    const clean = items
      .filter((i) => String(i.descripcion || '').trim() !== '')
      .map((i, n) => ({
        capitulo: i.capitulo,
        descripcion: String(i.descripcion).trim(),
        unidad: String(i.unidad || 'ud'),
        cantidad: Number(i.cantidad) || 0,
        precio_unitario: Number(i.precio_unitario) || 0,
        orden: n,
      }))
    setSaving(true)
    try {
      applyResponse(await api.projects.budget.save(projectId, { iva_pct: ivaPct, items: clean }))
      toast('success', 'Presupuesto guardado', `Total ${money(total)} €`)
    } catch (e) {
      toast('error', 'No se pudo guardar el presupuesto', e.message)
    } finally {
      setSaving(false)
    }
  }

  async function seed() {
    setConfirmSeed(false)
    try {
      applyResponse(await api.projects.budget.seed(projectId))
      toast('success', 'Partidas generadas desde el diseño', 'Completa los precios unitarios')
    } catch (e) {
      toast('error', 'No se pudo pre-rellenar', e.message)
    }
  }

  if (loading) return <Spinner label="Cargando presupuesto…" />

  return (
    <div className="sun-budget">
      <div className="sun-divider">Presupuesto</div>
      {items.length === 0 ? (
        <div className="sun-inline-note sun-inline-note--info">
          <Icon name="info" size={14} /> Sin partidas todavía. Pre-rellena desde el diseño o añade partidas a mano.
        </div>
      ) : (
        Object.entries(CAPITULOS).map(([num, titulo]) => {
          const capNum = Number(num)
          const rows = items.map((i, idx) => ({ ...i, idx })).filter((i) => i.capitulo === capNum)
          if (rows.length === 0 && !canEdit) return null
          const subtotal = rows.reduce((s, i) => s + (Number(i.cantidad) || 0) * (Number(i.precio_unitario) || 0), 0)
          return (
            <div key={num} className="sun-budget__chapter">
              <div className="sun-budget__chead">
                <strong>{num}. {titulo}</strong>
                {rows.length > 0 && <span className="num">{money(subtotal)} €</span>}
              </div>
              {rows.map((i) => (
                <div key={i.idx} className="sun-budget__row">
                  <input className="sun-input" placeholder="Descripción de la partida" value={i.descripcion}
                    disabled={!canEdit} onChange={(e) => updateItem(i.idx, { descripcion: e.target.value })} />
                  <input className="sun-input" aria-label="Unidad" value={i.unidad}
                    disabled={!canEdit} onChange={(e) => updateItem(i.idx, { unidad: e.target.value })} />
                  <input className="sun-input num" aria-label="Cantidad" type="number" min="0" step="any" value={i.cantidad}
                    disabled={!canEdit} onChange={(e) => updateItem(i.idx, { cantidad: e.target.value })} />
                  <input className="sun-input num" aria-label="Precio unitario (€)" type="number" min="0" step="any" value={i.precio_unitario}
                    disabled={!canEdit} onChange={(e) => updateItem(i.idx, { precio_unitario: e.target.value })} />
                  <span className="sun-budget__importe num">{money((Number(i.cantidad) || 0) * (Number(i.precio_unitario) || 0))}</span>
                  {canEdit && <IconBtn icon="trash-2" label="Quitar partida" size="sm" onClick={() => removeItem(i.idx)} />}
                </div>
              ))}
              {canEdit && (
                <button type="button" className="sun-budget__add" onClick={() => addItem(capNum)}>
                  <Icon name="plus" size={13} /> Añadir partida
                </button>
              )}
            </div>
          )
        })
      )}

      <div className="sun-budget__totals">
        <div className="sun-budget__trow"><span>Base imponible</span><span className="num">{money(base)} €</span></div>
        <div className="sun-budget__trow">
          <span>
            IVA{' '}
            <select className="sun-select sun-select--sm" style={{ width: 76, display: 'inline-block' }} aria-label="Tipo de IVA"
              value={ivaPct} disabled={!canEdit} onChange={(e) => { setIvaPct(Number(e.target.value)); setDirty(true) }}>
              {IVA_OPTS.map((v) => <option key={v} value={v}>{v} %</option>)}
            </select>
          </span>
          <span className="num">{money(iva)} €</span>
        </div>
        <div className="sun-budget__trow sun-budget__trow--total"><strong>Total presupuesto</strong><strong className="num">{money(total)} €</strong></div>
      </div>

      {canEdit && (
        <div className="sun-budget__actions">
          <Btn variant="secondary" icon="sparkles" onClick={() => (items.length ? setConfirmSeed(true) : seed())}>
            Pre-rellenar desde el diseño
          </Btn>
          <Btn variant="primary" icon="save" busy={saving} disabled={!dirty} onClick={save}>Guardar presupuesto</Btn>
        </div>
      )}

      <ConfirmDialog
        open={confirmSeed}
        title="Sustituir el presupuesto actual"
        description="Pre-rellenar desde el diseño reemplaza las partidas actuales por las generadas a partir de los equipos del proyecto."
        onClose={() => setConfirmSeed(false)}
        actions={[
          { label: 'Cancelar', variant: 'ghost', onClick: () => setConfirmSeed(false) },
          { label: 'Sustituir', variant: 'primary', icon: 'sparkles', onClick: seed },
        ]}
      />
    </div>
  )
}

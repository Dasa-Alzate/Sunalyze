import { useEffect, useId, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Btn, IconBtn, Icon, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

const CHAPTER_KEYS = ['1', '2', '3', '4']

export default function BudgetSettings() {
  const { t } = useTranslation('budget')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [laborFixed, setLaborFixed] = useState('')
  const [laborPerPanel, setLaborPerPanel] = useState('')
  const [inflationPct, setInflationPct] = useState('')
  const [lines, setLines] = useState([])
  const fixedId = useId()
  const perPanelId = useId()
  const inflationId = useId()

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    api.org.getBudgetProfile()
      .then((p) => {
        if (!alive) return
        setLaborFixed(p.labor_fixed || '')
        setLaborPerPanel(p.labor_per_panel || '')
        setInflationPct(p.equipment_inflation_pct || '')
        setLines(p.custom_lines || [])
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [])

  function updateLine(idx, patch) {
    setLines((list) => list.map((l, n) => (n === idx ? { ...l, ...patch } : l)))
  }

  function addLine() {
    setLines((list) => [...list, { capitulo: 4, descripcion: '', unidad: 'ud', cantidad: 1, precio_unitario: 0 }])
  }

  function removeLine(idx) {
    setLines((list) => list.filter((_, n) => n !== idx))
  }

  async function save() {
    const clean = lines
      .filter((l) => String(l.descripcion || '').trim() !== '')
      .map((l) => ({
        capitulo: Number(l.capitulo) || 4,
        descripcion: String(l.descripcion).trim(),
        unidad: String(l.unidad || 'ud'),
        cantidad: Number(l.cantidad) || 0,
        precio_unitario: Number(l.precio_unitario) || 0,
      }))
    setSaving(true)
    try {
      const p = await api.org.setBudgetProfile({
        labor_fixed: Number(laborFixed) || 0,
        labor_per_panel: Number(laborPerPanel) || 0,
        equipment_inflation_pct: Number(inflationPct) || 0,
        custom_lines: clean,
      })
      setLines(p.custom_lines || [])
      toast('success', t('saved'))
    } catch (e) {
      toast('error', t('saveError'), e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="sun-cfg-panel">
      <div className="sun-cfg-panel__head">
        <div>
          <h2 className="sun-cfg-panel__title">{t('title')}</h2>
          <p className="sun-cfg-panel__sub">{t('intro')}</p>
        </div>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      ) : loading ? (
        <Spinner />
      ) : (
        <div className="sun-brandform">
          <section className="sun-brandgroup sun-brandgroup--wide">
            <div className="sun-divider">{t('groups.labor')}</div>
            <div className="sun-budgetcfg__grid">
              <div className="sun-field">
                <label className="sun-field__label" htmlFor={fixedId}>{t('fields.laborFixed')}</label>
                <input id={fixedId} className="sun-input num" type="number" min="0" step="any"
                  value={laborFixed} aria-describedby={`${fixedId}-hint`}
                  onChange={(e) => setLaborFixed(e.target.value)} />
                <span id={`${fixedId}-hint`} className="sun-field__hint">{t('fields.laborFixedHint')}</span>
              </div>
              <div className="sun-field">
                <label className="sun-field__label" htmlFor={perPanelId}>{t('fields.laborPerPanel')}</label>
                <input id={perPanelId} className="sun-input num" type="number" min="0" step="any"
                  value={laborPerPanel} aria-describedby={`${perPanelId}-hint`}
                  onChange={(e) => setLaborPerPanel(e.target.value)} />
                <span id={`${perPanelId}-hint`} className="sun-field__hint">{t('fields.laborPerPanelHint')}</span>
              </div>
            </div>
          </section>

          <section className="sun-brandgroup">
            <div className="sun-divider">{t('groups.inflation')}</div>
            <div className="sun-field" style={{ maxWidth: 300 }}>
              <label className="sun-field__label" htmlFor={inflationId}>{t('fields.inflationPct')}</label>
              <input id={inflationId} className="sun-input num" type="number" min="0" max="100" step="any"
                value={inflationPct} aria-describedby={`${inflationId}-hint`}
                onChange={(e) => setInflationPct(e.target.value)} />
              <span id={`${inflationId}-hint`} className="sun-field__hint">{t('fields.inflationPctHint')}</span>
            </div>
          </section>

          <section className="sun-brandgroup sun-brandgroup--wide">
            <div className="sun-divider">{t('groups.lines')}</div>
            {lines.length === 0 ? (
              <div className="sun-inline-note sun-inline-note--info">
                <Icon name="info" size={14} /> {t('lines.empty')}
              </div>
            ) : (
              <div className="sun-budgetcfg__lines">
                <div className="sun-budgetcfg__line sun-budgetcfg__line--head" aria-hidden="true">
                  <span>{t('lines.chapter')}</span>
                  <span>{t('lines.description')}</span>
                  <span>{t('lines.unit')}</span>
                  <span className="num">{t('lines.qty')}</span>
                  <span className="num">{t('lines.price')}</span>
                  <span />
                </div>
                {lines.map((l, idx) => (
                  <div key={idx} className="sun-budgetcfg__line">
                    <select className="sun-select sun-select--sm" aria-label={t('lines.chapter')}
                      value={l.capitulo} onChange={(e) => updateLine(idx, { capitulo: Number(e.target.value) })}>
                      {CHAPTER_KEYS.map((c) => <option key={c} value={c}>{t(`chapters.${c}`)}</option>)}
                    </select>
                    <input className="sun-input" placeholder={t('lines.descriptionPlaceholder')} value={l.descripcion}
                      aria-label={t('lines.description')} onChange={(e) => updateLine(idx, { descripcion: e.target.value })} />
                    <input className="sun-input" aria-label={t('lines.unit')} value={l.unidad}
                      onChange={(e) => updateLine(idx, { unidad: e.target.value })} />
                    <input className="sun-input num" aria-label={t('lines.qty')} type="number" min="0" step="any"
                      value={l.cantidad} onChange={(e) => updateLine(idx, { cantidad: e.target.value })} />
                    <input className="sun-input num" aria-label={t('lines.price')} type="number" min="0" step="any"
                      value={l.precio_unitario} onChange={(e) => updateLine(idx, { precio_unitario: e.target.value })} />
                    <IconBtn icon="trash-2" label={t('lines.remove')} size="sm" onClick={() => removeLine(idx)} />
                  </div>
                ))}
              </div>
            )}
            <button type="button" className="sun-budget__add" onClick={addLine}>
              <Icon name="plus" size={13} /> {t('lines.add')}
            </button>
          </section>

          <div className="sun-brandform__foot">
            <Btn variant="primary" icon="save" busy={saving} onClick={save}>{t('save')}</Btn>
          </div>
        </div>
      )}
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Btn, Icon, Field, SelectField, Card, Spinner, ErrorState } from '@/shared/ui'
import { CircuitSvg } from '@/services/diagram-renderer'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

const SOLAR_TEMPLATES = {
  battery: 'solar-con-baterias',
  fuses: 'solar-con-fusibles',
  plain: 'solar-sin-fusibles',
}

const DEFAULT_FORM = {
  panel_model: '',
  panel_voc: '49',
  panel_isc: '13.8',
  panels_per_string: '10',
  num_strings: '2',
  dc_fuse_i: '15',
  dc_switch_v: '1000',
  dc_cable_section: '6 mm²',
  inverter_model: '',
  inverter_power: '5',
  inverter_output_i: '24',
  ac_phases: '1',
  ac_mcb_i: '25',
  ac_rcd_i: '40',
  ac_rcd_sensitivity: '30 mA',
  ac_cable_section: '6 mm²',
}

function solarTemplateFor(hasFuses, hasBattery) {
  if (hasBattery) return SOLAR_TEMPLATES.battery
  return hasFuses ? SOLAR_TEMPLATES.fuses : SOLAR_TEMPLATES.plain
}

function useDebounced(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(handle)
  }, [value, delay])
  return debounced
}

export default function CircuitDiagram({ panel = null, inverter = null, hasBattery: hasBatteryProp = false }) {
  const { t } = useTranslation('circuit')

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [templates, setTemplates] = useState([])
  const [template, setTemplate] = useState('solar-con-fusibles')
  const [hasFuses, setHasFuses] = useState(true)
  const [hasBattery, setHasBattery] = useState(false)
  const [form, setForm] = useState(DEFAULT_FORM)

  const isSolar = template.startsWith('solar-')

  useEffect(() => {
    let alive = true
    setLoading(true)
    setLoadError(null)
    api.circuit.templates()
      .then((tmpls) => { if (alive) setTemplates(tmpls) })
      .catch((e) => alive && setLoadError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [reloadKey])

  useEffect(() => {
    setHasBattery(hasBatteryProp)
    setTemplate(solarTemplateFor(true, hasBatteryProp))
    setForm((f) => ({
      ...f,
      panel_model: panel?.nombre ?? f.panel_model,
      panel_voc: panel?.voc != null ? String(panel.voc) : f.panel_voc,
      panel_isc: panel?.isc != null ? String(panel.isc) : f.panel_isc,
      inverter_model: inverter?.nombre ?? f.inverter_model,
      inverter_power: inverter?.power != null ? String(inverter.power) : f.inverter_power,
      inverter_output_i: inverter?.I_max_output != null ? String(inverter.I_max_output) : f.inverter_output_i,
    }))
  }, [panel, inverter, hasBatteryProp])

  function patch(p) { setForm((f) => ({ ...f, ...p })) }

  function pickTemplate(name) {
    setTemplate(name)
    if (name === SOLAR_TEMPLATES.battery) { setHasBattery(true); setHasFuses(true) }
    else if (name === SOLAR_TEMPLATES.fuses) { setHasBattery(false); setHasFuses(true) }
    else if (name === SOLAR_TEMPLATES.plain || name === 'solar-basico') { setHasBattery(false); setHasFuses(false) }
  }

  function toggleFuses(next) {
    setHasFuses(next)
    if (isSolar) setTemplate(solarTemplateFor(next, hasBattery))
  }

  function toggleBattery(next) {
    setHasBattery(next)
    if (isSolar) setTemplate(solarTemplateFor(hasFuses, next))
  }

  const params = useMemo(() => ({
    ...form,
    has_fuses: hasFuses ? 'true' : 'false',
    has_battery: hasBattery ? 'true' : 'false',
    sheet: '1',
  }), [form, hasFuses, hasBattery])

  const debouncedParams = useDebounced(params, 350)
  const debouncedTemplate = useDebounced(template, 350)

  async function downloadSvg() {
    const url = api.circuit.svgUrl(debouncedTemplate, debouncedParams)
    try {
      const res = await fetch(url, { credentials: 'include' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const svg = await res.text()
      const blob = new Blob([svg], { type: 'image/svg+xml' })
      const href = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = href
      a.download = `${debouncedTemplate}.svg`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(href)
    } catch (e) {
      toast('error', t('preview.error'), e.message)
    }
  }

  if (loading) {
    return <Spinner label={t('preview.loading')} />
  }
  if (loadError) {
    return <ErrorState message={loadError} onRetry={() => setReloadKey((k) => k + 1)} />
  }

  return (
    <>
      <p className="sun-help" style={{ marginBottom: 'var(--space-4)' }}>{t('intro')}</p>
      <div className="sun-circuit">
        <Card className="sun-circuit__controls">
          <SelectField
            label={t('template.label')}
            value={template}
            onChange={(e) => pickTemplate(e.target.value)}
            options={templates.map((o) => ({ value: o.name, label: o.label }))}
          />
          <div className="sun-circuit__toggles">
            <label className="sun-check">
              <input type="checkbox" checked={hasFuses} disabled={!isSolar} onChange={(e) => toggleFuses(e.target.checked)} />
              <span className="sun-check__box"><Icon name="check" size={13} /></span>
              <span>{t('toggles.fuses')}</span>
            </label>
            <label className="sun-check">
              <input type="checkbox" checked={hasBattery} disabled={!isSolar} onChange={(e) => toggleBattery(e.target.checked)} />
              <span className="sun-check__box"><Icon name="check" size={13} /></span>
              <span>{t('toggles.battery')}</span>
            </label>
          </div>

          <div className="sun-divider">{t('sections.dc')}</div>
          <div className="sun-circuit__grid">
            <Field label={t('fields.panel_model')} value={form.panel_model} onChange={(e) => patch({ panel_model: e.target.value })} />
            <Field label={t('fields.panel_voc')} numeric type="number" step="any" value={form.panel_voc} onChange={(e) => patch({ panel_voc: e.target.value })} hint="V" />
            <Field label={t('fields.panel_isc')} numeric type="number" step="any" value={form.panel_isc} onChange={(e) => patch({ panel_isc: e.target.value })} hint="A" />
            <Field label={t('fields.panels_per_string')} numeric type="number" step="1" min="1" value={form.panels_per_string} onChange={(e) => patch({ panels_per_string: e.target.value })} />
            <Field label={t('fields.num_strings')} numeric type="number" step="1" min="1" value={form.num_strings} onChange={(e) => patch({ num_strings: e.target.value })} />
            <Field label={t('fields.dc_fuse_i')} numeric type="number" step="any" value={form.dc_fuse_i} onChange={(e) => patch({ dc_fuse_i: e.target.value })} hint="A" />
            <Field label={t('fields.dc_switch_v')} numeric type="number" step="any" value={form.dc_switch_v} onChange={(e) => patch({ dc_switch_v: e.target.value })} hint="V" />
            <Field label={t('fields.dc_cable_section')} value={form.dc_cable_section} onChange={(e) => patch({ dc_cable_section: e.target.value })} />
          </div>

          <div className="sun-divider">{t('sections.ac')}</div>
          <div className="sun-circuit__grid">
            <Field label={t('fields.inverter_model')} value={form.inverter_model} onChange={(e) => patch({ inverter_model: e.target.value })} />
            <Field label={t('fields.inverter_power')} numeric type="number" step="any" value={form.inverter_power} onChange={(e) => patch({ inverter_power: e.target.value })} hint="kW" />
            <Field label={t('fields.inverter_output_i')} numeric type="number" step="any" value={form.inverter_output_i} onChange={(e) => patch({ inverter_output_i: e.target.value })} hint="A" />
            <SelectField label={t('fields.ac_phases')} value={form.ac_phases} onChange={(e) => patch({ ac_phases: e.target.value })}
              options={[{ value: '1', label: t('phases.mono') }, { value: '3', label: t('phases.tri') }]} />
            <Field label={t('fields.ac_mcb_i')} numeric type="number" step="any" value={form.ac_mcb_i} onChange={(e) => patch({ ac_mcb_i: e.target.value })} hint="A" />
            <Field label={t('fields.ac_rcd_i')} numeric type="number" step="any" value={form.ac_rcd_i} onChange={(e) => patch({ ac_rcd_i: e.target.value })} hint="A" />
            <Field label={t('fields.ac_rcd_sensitivity')} value={form.ac_rcd_sensitivity} onChange={(e) => patch({ ac_rcd_sensitivity: e.target.value })} />
            <Field label={t('fields.ac_cable_section')} value={form.ac_cable_section} onChange={(e) => patch({ ac_cable_section: e.target.value })} />
          </div>
        </Card>

        <Card className="sun-circuit__preview">
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--space-3)' }}>
            <div className="sun-divider" style={{ flex: 1, marginBottom: 0 }}>{t('preview.title')}</div>
            <Btn variant="secondary" size="sm" icon="download" onClick={downloadSvg}>{t('actions.download')}</Btn>
          </div>
          <div className="sun-circuit__canvas" role="img" aria-label={t('preview.alt')}>
            <CircuitSvg
              type={debouncedTemplate}
              params={debouncedParams}
              fallback={<div className="sun-inline-note sun-inline-note--danger"><Icon name="alert-triangle" size={14} />{t('preview.error')}</div>}
            />
          </div>
        </Card>
      </div>
    </>
  )
}

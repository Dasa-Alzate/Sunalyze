import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Topbar } from '@/shared/ui'
import { Btn, IconBtn, Icon, Dot, Field, SelectField, Spinner, ErrorState } from '@/shared/ui'
import { api, csrfToken } from '@/api/client'
import { toast } from '@/services/toast'
import { MemoriaDocument } from '@/services/template-renderer'
import { useAuth } from '@/services/auth'

const SECTIONS = [
  {
    id: 'cliente', title: 'Cliente y emplazamiento',
    fields: [
      { key: 'client_name', label: 'Nombre del cliente', required: true },
      { key: 'location', label: 'Localidad', required: true },
      { key: 'address', label: 'Dirección', required: true },
      { key: 'zipcode', label: 'Código postal', required: true },
      { key: 'catastral_reference', label: 'Referencia catastral', required: true },
    ],
  },
  {
    id: 'contrato', title: 'Contrato eléctrico',
    fields: [
      { key: 'energy_company_name', label: 'Compañía', select: ['Iberdrola', 'Endesa', 'Naturgy', 'Otra'], required: true },
      { key: 'energy_company_cups', label: 'CUPS', required: true },
      { key: 'hired_power_kw', label: 'Potencia contratada (kW)', num: true, required: true },
      { key: 'input_v', label: 'Tensión (V)', num: true, required: true },
      { key: 'input_v_type', label: 'Tipo de voltaje', select: ['Monofásica', 'Trifásica'], required: true },
      { key: 'inyection_type', label: 'Objetivo del sistema', select: ['Con inyección de excedentes', 'Sin inyección'], required: true },
    ],
  },
  {
    id: 'config', title: 'Configuración',
    fields: [
      { key: 'panels_peak_power_kw', label: 'Potencia pico (kWp)', num: true, required: true },
      { key: 'panels_number', label: 'Nº de paneles', num: true, required: true },
      { key: 'mppt_inputs', label: 'Entradas MPPT', num: true, required: true },
      { key: 'panels_place', label: 'Ubicación de paneles', required: true },
      { key: 'panels_disposition', label: 'Disposición', required: true },
      { key: 'inverter_place', label: 'Ubicación del inversor', required: true },
    ],
  },
  {
    id: 'protecciones', title: 'Protecciones',
    fields: [
      { key: 'protections_dc_thermal_v_max', label: 'Magnetotérmico DC · V máx', num: true, required: true },
      { key: 'protections_dc_breaker_i', label: 'Magnetotérmico DC (A)', num: true, required: true },
      { key: 'protections_ac_thermal_i', label: 'Magnetotérmico AC (A)', num: true, required: true },
      { key: 'protections_ac_diff_i', label: 'Diferencial AC (A)', num: true, required: true },
      { key: 'protections_ac_transitory_surge_model', label: 'Protector sobretensiones', required: true },
      { key: 'wire_ground_length', label: 'Longitud cable de tierra (m)', num: true, required: true },
    ],
  },
]

const ALL_FIELDS = SECTIONS.flatMap((s) => s.fields)

function seed(project, battery) {
  const p = project || {}
  const b = battery || {}
  return {
    client_name: p.cliente || '',
    location: p.localidad || 'Alicante',
    address: p.direccion || '',
    zipcode: '03001',
    catastral_reference: p.referencia_catastral || '',
    energy_company_name: p.compania || 'Iberdrola',
    energy_company_cups: p.cups || '',
    hired_power_kw: p.potencia_contratada ?? '',
    input_v: '230',
    input_v_type: p.tipo_voltaje || 'Monofásica',
    inyection_type: 'Con inyección de excedentes',
    panels_peak_power_kw: p.kwp ?? '',
    panels_number: p.n_paneles ?? '',
    mppt_inputs: '2',
    panels_place: 'Cubierta',
    panels_disposition: p.coplanar ? 'Coplanar' : 'Estructura inclinada',
    inverter_place: 'Pared exterior',
    protections_dc_thermal_v_max: '600',
    protections_dc_breaker_i: '16',
    protections_ac_thermal_i: '16',
    protections_ac_diff_i: '25',
    protections_ac_transitory_surge_model: 'Citel DS50VGP-AC',
    wire_ground_length: '10',
    battery_nombre: p.battery_nombre || b.nombre || '',
    battery_quantity: p.battery_quantity ?? '',
    battery_capacity_kwh: b.capacity_kwh ?? '',
    battery_usable_kwh: b.usable_kwh ?? '',
    battery_power_kw: b.power_kw ?? '',
    battery_technology: b.technology || '',
  }
}

const BATTERY_KEYS = ['battery_nombre', 'battery_quantity', 'battery_capacity_kwh', 'battery_usable_kwh', 'battery_power_kw', 'battery_technology']

export default function MemoriaPreview() {
  const { id } = useParams()
  const nav = useNavigate()
  const { can } = useAuth()
  const canSign = can('memoria:sign')
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(!!id)
  const [error, setError] = useState(null)
  const [values, setValues] = useState(() => seed(null))
  const [open, setOpen] = useState('cliente')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) { setValues(seed(null)); return }
    setLoading(true)
    setError(null)
    Promise.all([api.projects.get(Number(id)), api.batteries.list().catch(() => [])])
      .then(([proj, bats]) => {
        setProject(proj)
        const battery = proj.battery_id ? (bats || []).find((b) => b.id === proj.battery_id) : null
        setValues(seed(proj, battery))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.value }))

  function sectionState(section) {
    const reqs = section.fields.filter((f) => f.required)
    const filled = reqs.filter((f) => String(values[f.key] ?? '').trim() !== '')
    if (filled.length === reqs.length) return 'valid'
    if (filled.length === 0) return 'pending'
    return 'warn'
  }

  function missingNote(section) {
    const reqs = section.fields.filter((f) => f.required)
    const miss = reqs.filter((f) => String(values[f.key] ?? '').trim() === '')
    return miss.length ? `${miss.length} pendiente${miss.length > 1 ? 's' : ''}` : null
  }

  async function saveToProject(estado) {
    if (!id) { toast('info', 'Sin proyecto', 'Genera la memoria desde un proyecto guardado para persistir los datos'); return }
    setSaving(true)
    try {
      const proj = await api.projects.update(Number(id), {
        cliente: values.client_name || project?.cliente,
        localidad: values.location,
        direccion: values.address,
        referencia_catastral: values.catastral_reference,
        cups: values.energy_company_cups,
        compania: values.energy_company_name,
        potencia_contratada: values.hired_power_kw === '' ? null : Number(values.hired_power_kw),
        tipo_voltaje: values.input_v_type,
        ...(estado ? { estado } : {}),
      })
      setProject(proj)
      toast('success', 'Datos guardados')
    } catch (e) {
      toast('error', 'No se pudo guardar', e.message)
    } finally {
      setSaving(false)
    }
  }

  async function generarPDF() {
    const missing = ALL_FIELDS.filter((f) => f.required && String(values[f.key] ?? '').trim() === '')
    if (missing.length) {
      toast('warning', 'Faltan campos obligatorios', missing.map((f) => f.label).slice(0, 3).join(', ') + (missing.length > 3 ? '…' : ''))
      const sec = SECTIONS.find((s) => s.fields.some((f) => missing.includes(f)))
      if (sec) setOpen(sec.id)
      return
    }
    if (id) saveToProject('memoria')
    const fd = new FormData()
    fd.append('csrf_token', csrfToken())
    ALL_FIELDS.forEach((f) => fd.append(f.key, values[f.key] ?? ''))
    BATTERY_KEYS.forEach((k) => { if (values[k] !== '' && values[k] != null) fd.append(k, values[k]) })
    if (project?.panel_id) fd.append('panel_id', project.panel_id)
    if (project?.inverter_id) fd.append('inverter_id', project.inverter_id)
    if (project?.battery_id) { fd.append('battery_id', project.battery_id); fd.append('battery_quantity', project.battery_quantity ?? 1) }
    toast('info', 'Generando memoria…', 'Se abrirá el PDF en una pestaña nueva')
    try {
      const res = await fetch('/imprimir/memoria-pdf', {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': csrfToken() },
        body: fd,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        const detail = body?.details?.length
          ? body.details.map((d) => `${d.field}: ${d.msg}`).join('; ')
          : (body?.error || `Error ${res.status}`)
        toast('error', 'No se pudo generar la memoria', detail)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      toast('error', 'No se pudo generar la memoria', e.message)
    }
  }

  if (loading) return (<><Topbar title="Memoria" crumb="Proyectos" /><div className="sun-content"><Spinner label="Cargando…" /></div></>)
  if (error) return (<><Topbar title="Memoria" crumb="Proyectos" /><div className="sun-content"><ErrorState message={error} onRetry={() => nav(0)} /></div></>)

  return (
    <>
      <Topbar
        title="Memoria técnica"
        crumb={project ? project.cliente : 'Proyectos'}
        actions={
          <>
            {id && <Btn variant="secondary" icon="save" data-busy={saving} disabled={saving} onClick={() => saveToProject()}>Guardar</Btn>}
            <Btn variant="primary" icon="file-text" onClick={generarPDF} disabled={!canSign} title={canSign ? undefined : "Tu rol no permite firmar/generar la memoria"}>Generar PDF</Btn>
          </>
        }
      />
      <div className="sun-content">
        <div className="sun-memoria">
          <div>
            <div className="sun-memoria__sections">
              {SECTIONS.map((s) => {
                const st = sectionState(s)
                const note = missingNote(s)
                return (
                  <div key={s.id} className={`sun-msection${open === s.id ? ' sun-msection--active' : ''}`}>
                    <button type="button" className="sun-msection__head" aria-expanded={open === s.id} onClick={() => setOpen(open === s.id ? null : s.id)}>
                      <Dot state={st} />
                      <span className="sun-msection__title">{s.title}</span>
                      {note && <span className="sun-badge sun-badge--warning"><Icon name="alert-triangle" size={12} />{note}</span>}
                      <Icon name={open === s.id ? 'chevron-down' : 'chevron-right'} size={16} style={{ color: 'var(--text-subtle)' }} />
                    </button>
                    {open === s.id && (
                      <div className="sun-msection__body">
                        <div className="sun-speclist" style={{ marginTop: 'var(--space-4)' }}>
                          {s.fields.map((f) => (
                            f.select ? (
                              <SelectField key={f.key} label={f.label} options={f.select} value={values[f.key]} onChange={set(f.key)} />
                            ) : (
                              <Field key={f.key} label={f.label} required={f.required} numeric={f.num}
                                type={f.num ? 'number' : 'text'} step={f.num ? 'any' : undefined}
                                value={values[f.key]} onChange={set(f.key)} />
                            )
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <div style={{ marginTop: 'var(--space-5)', display: 'flex', gap: 'var(--space-3)' }}>
              <Btn variant="primary" icon="file-text" onClick={generarPDF} disabled={!canSign} title={canSign ? undefined : "Tu rol no permite firmar/generar la memoria"}>Generar PDF</Btn>
              {!id && <span style={{ alignSelf: 'center', fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Abre la memoria desde un proyecto para guardar los datos.</span>}
            </div>
          </div>

          <div className="sun-preview">
            <MemoriaDocument values={values} />
            <div style={{ textAlign: 'center', marginTop: 'var(--space-3)', fontSize: 'var(--text-xs)', color: 'var(--text-subtle)' }}>
              Vista previa en vivo — nadie genera a ciegas
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

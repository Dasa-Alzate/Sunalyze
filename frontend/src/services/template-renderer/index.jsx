import { UnifilarStrip } from '@/services/diagram-renderer'

export function MemoriaDocument({ values = {} }) {
  const name = values.client_name || 'Cliente'
  const addr = [values.address, values.location].filter(Boolean).join(', ')
  return (
    <div className="sun-page">
      <h2>Memoria Técnica · Instalación Fotovoltaica</h2>
      <p style={{ fontWeight: 700, color: 'var(--ink-800)' }}>{name}{addr ? ` — ${addr}` : ''}</p>
      <p>CUPS {values.energy_company_cups || '—'} · Ref. catastral {values.catastral_reference || '—'} · {values.energy_company_name || '—'}</p>
      <p style={{ fontWeight: 700, color: 'var(--ink-800)', marginTop: 14 }}>1. Descripción de la instalación</p>
      <p>
        Instalación fotovoltaica de autoconsumo de {values.panels_peak_power_kw || '—'} kWp con {values.panels_number || '—'} módulos
        sobre {String(values.panels_place || '—').toLowerCase()}, {String(values.panels_disposition || '—').toLowerCase()}. {values.inyection_type || ''}.
        Potencia contratada {values.hired_power_kw || '—'} kW, suministro {String(values.input_v_type || '—').toLowerCase()} a {values.input_v || '—'} V.
      </p>
      {values.battery_nombre && (
        <>
          <p style={{ fontWeight: 700, color: 'var(--ink-800)', marginTop: 14 }}>2. Acumulación</p>
          <p>
            Sistema de acumulación con {values.battery_quantity > 1 ? `${values.battery_quantity} × ` : ''}{values.battery_nombre}
            {values.battery_capacity_kwh ? `, capacidad nominal ${values.battery_capacity_kwh} kWh` : ''}
            {values.battery_usable_kwh ? ` (${values.battery_usable_kwh} kWh útiles)` : ''}
            {values.battery_power_kw ? `, potencia ${values.battery_power_kw} kW` : ''}
            {values.battery_technology ? `, tecnología ${values.battery_technology}` : ''}.
          </p>
        </>
      )}
      <p style={{ fontWeight: 700, color: 'var(--ink-800)', marginTop: 14 }}>{values.battery_nombre ? '3' : '2'}. Esquema unifilar</p>
      <div className="sun-page__diagram">
        <UnifilarStrip battery={!!values.battery_nombre} />
      </div>
    </div>
  )
}

export const EMAIL_TEMPLATES = [
  { id: 'welcome', label: 'Bienvenida', desc: 'Onboarding tras crear cuenta' },
  { id: 'reset-password', label: 'Recuperar contraseña', desc: 'Enlace de restablecimiento' },
  { id: 'memoria-ready', label: 'Memoria lista', desc: 'Aviso de memoria generada' },
]

export function emailPreviewUrl(id) {
  return `/api/emails/${id}/preview`
}

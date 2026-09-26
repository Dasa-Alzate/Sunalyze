import { useEffect, useMemo, useState } from 'react'
import { Badge, Btn, SelectField } from '@/shared/ui'
import { api } from '@/api/client'
import { ImportProfileModal } from './ImportProfileModal'
import { ProfileSparkline } from './ProfileSparkline'
import './consumption.css'

export const KIND_LABELS = {
  annual: 'Curva anual',
  day: 'Día tipo',
  daytypes: 'Día tipo',
  week: 'Semana tipo',
  month: 'Mes medido',
  seasonal: 'Estacional',
}

export function originBadge(profile) {
  if (profile.origin === 'file') return { tone: 'success', label: 'Medido' }
  if (profile.is_global) return { tone: 'info', label: 'Perfil típico' }
  return { tone: 'warning', label: 'Estimado' }
}

export function ConsumptionProfileSection({ value, onChange }) {
  const [profiles, setProfiles] = useState(null)
  const [preview, setPreview] = useState(null)
  const [importing, setImporting] = useState(false)

  async function load() {
    try {
      setProfiles(await api.consumptionProfiles.list())
    } catch {
      setProfiles([])
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!value) { setPreview(null); return undefined }
    let alive = true
    api.consumptionProfiles.preview(value)
      .then((p) => { if (alive) setPreview(p) })
      .catch(() => { if (alive) setPreview(null) })
    return () => { alive = false }
  }, [value])

  const selected = useMemo(
    () => (profiles || []).find((p) => p.id === Number(value)) || null,
    [profiles, value],
  )
  const curated = (profiles || []).filter((p) => p.is_global)
  const own = (profiles || []).filter((p) => !p.is_global)

  return (
    <div className="cp-section">
      <div className="cp-section__row">
        <SelectField
          label="Perfil de consumo"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        >
          <option value="">Sin perfil (solo dimensionado energético)</option>
          {own.length > 0 && (
            <optgroup label="De tu organización">
              {own.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </optgroup>
          )}
          {curated.length > 0 && (
            <optgroup label="Perfiles típicos">
              {curated.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </optgroup>
          )}
        </SelectField>
        <Btn variant="secondary" icon="upload" onClick={() => setImporting(true)}>Subir CSV</Btn>
      </div>
      {selected && preview && (
        <div className="cp-section__preview sun-reveal">
          <ProfileSparkline preview={preview} />
          <div className="cp-section__meta">
            <Badge tone={originBadge(selected).tone}>{originBadge(selected).label}</Badge>
            <span>{KIND_LABELS[selected.kind] || selected.kind}</span>
            {preview.annual_kwh_hint != null && (
              <span>muestra de {Math.round(preview.annual_kwh_hint).toLocaleString('es-ES')} kWh/año</span>
            )}
          </div>
          <p className="cp-section__legend">
            <span className="cp-dot cp-dot--year" /> media anual ·{' '}
            <span className="cp-dot cp-dot--winter" /> invierno ·{' '}
            <span className="cp-dot cp-dot--summer" /> verano
          </p>
        </div>
      )}
      {!value && (
        <p className="cp-section__hint">
          Con perfil, el análisis podrá calcular el autoconsumo real y el aporte económico de la batería.
        </p>
      )}
      {importing && (
        <ImportProfileModal
          onClose={() => setImporting(false)}
          onImported={(profile) => { setImporting(false); load().then(() => onChange(profile.id)) }}
        />
      )}
    </div>
  )
}

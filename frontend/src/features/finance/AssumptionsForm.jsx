import { Field, SelectField, Icon } from '@/shared/ui'
import { CCAA_OPTIONS, MUNICIPIO_OPTIONS } from './constants'

function NumField({ label, name, value, onChange, hint, step }) {
  return (
    <Field
      label={label}
      type="number"
      numeric
      step={step}
      value={value}
      hint={hint}
      onChange={(e) => onChange(name, e.target.value)}
    />
  )
}

export default function AssumptionsForm({ form, onChange }) {
  function set(name, value) {
    onChange({ ...form, [name]: value })
  }

  return (
    <div className="finance-form">
      <fieldset className="finance-fieldset">
        <legend className="sun-section-title"><Icon name="banknote" size={15} />Inversión (CAPEX)</legend>
        <SelectField
          label="Modo de CAPEX"
          value={form.capexMode}
          onChange={(e) => set('capexMode', e.target.value)}
          options={[
            { value: 'total', label: 'Total' },
            { value: 'breakdown', label: 'Desglose (equipo / mano de obra / legalización)' },
          ]}
        />
        {form.capexMode === 'total' ? (
          <NumField label="CAPEX total (€, sin IVA)" name="capex_total" value={form.capex_total} onChange={set} />
        ) : (
          <>
            <NumField label="Equipo (€)" name="capex_equipment" value={form.capex_equipment} onChange={set} />
            <NumField label="Mano de obra (€)" name="capex_labor" value={form.capex_labor} onChange={set} />
            <NumField label="Legalización (€)" name="capex_legalization" value={form.capex_legalization} onChange={set} />
          </>
        )}
        <NumField label="IVA (proporción)" name="iva_pct" value={form.iva_pct} onChange={set} step="0.01" hint="0,21 = 21 %" />
      </fieldset>

      <fieldset className="finance-fieldset">
        <legend className="sun-section-title"><Icon name="zap" size={15} />Energía y tarifas</legend>
        <NumField label="Tarifa eléctrica (€/kWh)" name="tariff_eur_kwh" value={form.tariff_eur_kwh} onChange={set} step="0.01" />
        <NumField label="Consumo anual (kWh)" name="annual_consumption_kwh" value={form.annual_consumption_kwh} onChange={set} hint="Opcional; limita el ahorro por excedentes" />
        <NumField label="Precio de excedentes (€/kWh)" name="surplus_price_eur_kwh" value={form.surplus_price_eur_kwh} onChange={set} step="0.01" />
        <Field label="Ratio de autoconsumo">
          <label className="finance-check">
            <input
              type="checkbox"
              checked={form.autoRatio}
              onChange={(e) => set('autoRatio', e.target.checked)}
            />
            <span>Automático del análisis del proyecto</span>
          </label>
        </Field>
        {!form.autoRatio && (
          <NumField label="Ratio de autoconsumo (proporción)" name="self_consumption_ratio" value={form.self_consumption_ratio} onChange={set} step="0.05" hint="0,65 = 65 %" />
        )}
      </fieldset>

      <fieldset className="finance-fieldset">
        <legend className="sun-section-title"><Icon name="sliders-horizontal" size={15} />Supuestos del estudio</legend>
        <NumField label="Vida útil (años)" name="lifetime_years" value={form.lifetime_years} onChange={set} />
        <NumField label="Tasa de descuento (proporción)" name="discount_rate" value={form.discount_rate} onChange={set} step="0.005" />
        <NumField label="IPC / escalada de tarifa (proporción)" name="tariff_escalation_pct" value={form.tariff_escalation_pct} onChange={set} step="0.005" />
        <NumField label="Degradación anual del panel (proporción)" name="panel_degradation_pct" value={form.panel_degradation_pct} onChange={set} step="0.001" />
        <NumField label="O&M anual (€)" name="om_cost_eur_year" value={form.om_cost_eur_year} onChange={set} />
        <NumField label="Factor de emisión (kg CO₂/kWh)" name="emission_factor_kg_kwh" value={form.emission_factor_kg_kwh} onChange={set} step="0.01" />
      </fieldset>

      <fieldset className="finance-fieldset">
        <legend className="sun-section-title"><Icon name="landmark" size={15} />Financiación</legend>
        <Field label="Forma de pago">
          <label className="finance-check">
            <input
              type="checkbox"
              checked={form.financed}
              onChange={(e) => set('financed', e.target.checked)}
            />
            <span>{form.financed ? 'Financiado' : 'Al contado'}</span>
          </label>
        </Field>
        {form.financed && (
          <>
            <NumField label="Importe financiado (€)" name="financing_amount" value={form.financing_amount} onChange={set} />
            <NumField label="Interés anual (proporción)" name="financing_interest_rate" value={form.financing_interest_rate} onChange={set} step="0.005" />
            <NumField label="Plazo (años)" name="financing_term_years" value={form.financing_term_years} onChange={set} />
          </>
        )}
      </fieldset>

      <fieldset className="finance-fieldset">
        <legend className="sun-section-title"><Icon name="badge-percent" size={15} />Subvenciones</legend>
        <Field label="Aplicar subvenciones">
          <label className="finance-check">
            <input
              type="checkbox"
              checked={form.apply_subsidies}
              onChange={(e) => set('apply_subsidies', e.target.checked)}
            />
            <span>Incluir ayudas (mejor caso indicativo)</span>
          </label>
        </Field>
        {form.apply_subsidies && (
          <>
            <div
              className="sun-card sun-card--flat"
              role="note"
              style={{ background: 'var(--warning-soft)', color: 'var(--warning-fg)', padding: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)' }}
            >
              <Icon name="alert-triangle" size={16} />
              <span style={{ fontSize: 'var(--text-sm)' }}>
                El total de subvenciones es un mejor caso indicativo: no modela incompatibilidades
                ni requisitos administrativos reales.
              </span>
            </div>
            <SelectField
              label="Comunidad autónoma"
              value={form.ccaa}
              onChange={(e) => set('ccaa', e.target.value)}
              options={CCAA_OPTIONS}
            />
            <SelectField
              label="Municipio"
              value={form.municipio}
              onChange={(e) => set('municipio', e.target.value)}
              options={MUNICIPIO_OPTIONS}
            />
          </>
        )}
      </fieldset>
    </div>
  )
}

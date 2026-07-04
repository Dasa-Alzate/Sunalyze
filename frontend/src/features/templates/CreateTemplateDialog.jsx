import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Scrim, Btn, Field, SelectField } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { DOCUMENT_KINDS, TEMPLATE_STAGES } from './constants'

export default function CreateTemplateDialog({ onCreated, onClose }) {
  const { t } = useTranslation('templates')
  const { t: tc } = useTranslation('common')
  const [kindOptions, setKindOptions] = useState(DOCUMENT_KINDS)
  const [name, setName] = useState('')
  const [kind, setKind] = useState(DOCUMENT_KINDS[0].value)
  const [description, setDescription] = useState('')
  const [country, setCountry] = useState('')
  const [region, setRegion] = useState('')
  const [requiredBy, setRequiredBy] = useState('')
  const [stage, setStage] = useState('')
  const [locale, setLocale] = useState('')
  const [currency, setCurrency] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    api.templates.kinds()
      .then((rows) => {
        if (!alive || !Array.isArray(rows) || rows.length === 0) return
        const opts = rows.map((r) => ({ value: r.key, label: r.label }))
        setKindOptions(opts)
        setKind(opts[0].value)
      })
      .catch((e) => toast('error', tc('state.errorTitle'), e.message))
    return () => { alive = false }
  }, [])

  async function submit() {
    if (!name.trim()) { toast('warning', tc('validation.required')); return }
    setBusy(true)
    try {
      const tpl = await api.templates.create({
        name: name.trim(),
        kind,
        description: description.trim(),
        country: country.trim() || null,
        region: region.trim() || null,
        required_by: requiredBy.trim() || null,
        stage: stage || null,
        locale: locale.trim() || null,
        currency: currency.trim() || null,
      })
      toast('success', t('create.saved'))
      onCreated(tpl)
    } catch (e) {
      toast('error', tc('state.errorTitle'), e.message)
    } finally {
      setBusy(false)
    }
  }

  const stageOptions = [
    { value: '', label: t('fields.stagePlaceholder') },
    ...TEMPLATE_STAGES.map((s) => ({ value: s.value, label: s.label })),
  ]

  return (
    <Scrim label={t('create.title')} onClose={onClose}>
      <div className="sun-drawer" role="document">
        <header className="sun-drawer__head"><h3>{t('create.title')}</h3></header>
        <div className="sun-drawer__body">
          <div className="sun-speclist">
            <Field label={t('fields.name')} required value={name} onChange={(e) => setName(e.target.value)} />
            <SelectField label={t('fields.kind')} value={kind} onChange={(e) => setKind(e.target.value)} options={kindOptions} />
            <Field label={t('fields.description')} value={description} onChange={(e) => setDescription(e.target.value)} />
            <Field label={t('fields.country')} value={country} onChange={(e) => setCountry(e.target.value)} />
            <Field label={t('fields.region')} value={region} onChange={(e) => setRegion(e.target.value)} />
            <Field label={t('fields.requiredBy')} value={requiredBy} onChange={(e) => setRequiredBy(e.target.value)} />
            <SelectField label={t('fields.stage')} value={stage} onChange={(e) => setStage(e.target.value)} options={stageOptions} />
            <Field label={t('fields.locale')} hint={t('fields.localeHint')} value={locale} onChange={(e) => setLocale(e.target.value)} />
            <Field label={t('fields.currency')} hint={t('fields.currencyHint')} value={currency} onChange={(e) => setCurrency(e.target.value)} />
          </div>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>{tc('actions.cancel')}</Btn>
          <Btn variant="primary" icon="plus" busy={busy} onClick={submit}>{tc('actions.create')}</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

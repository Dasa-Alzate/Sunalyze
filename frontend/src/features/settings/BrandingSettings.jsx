import { useEffect, useId, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Btn, Icon, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'

function isHex(value) {
  return /^#[0-9a-fA-F]{6}$/.test(value || '')
}

export default function BrandingSettings() {
  const { t } = useTranslation('branding')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [logoPath, setLogoPath] = useState('')
  const [logoVersion, setLogoVersion] = useState(0)
  const [primaryColor, setPrimaryColor] = useState('')
  const [footerText, setFooterText] = useState('')
  const [projectPrefix, setProjectPrefix] = useState('')
  const fileRef = useRef(null)
  const logoId = useId()
  const colorPickerId = useId()
  const footerId = useId()
  const prefixId = useId()

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    api.org.getBranding()
      .then((b) => {
        if (!alive) return
        setLogoPath(b.logo_path || '')
        setPrimaryColor(b.primary_color || '')
        setFooterText(b.footer_text || '')
        setProjectPrefix(b.project_prefix || '')
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [])

  async function save() {
    setSaving(true)
    try {
      await api.org.setBranding({
        primary_color: primaryColor.trim() || null,
        footer_text: footerText.trim() || null,
        project_prefix: projectPrefix.trim() || null,
      })
      toast('success', t('saved'))
    } catch (e) {
      toast('error', t('saveError'), e.message)
    } finally {
      setSaving(false)
    }
  }

  async function onLogoPicked(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const b = await api.org.uploadLogo(file)
      setLogoPath(b.logo_path || '')
      setLogoVersion((v) => v + 1)
      toast('success', t('logo.uploaded'))
    } catch (err) {
      toast('error', t('logo.uploadError'), err.message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const logoSrc = logoPath ? `${api.org.logoUrl()}?v=${logoVersion}` : ''

  return (
    <div className="sun-cfg-panel">
      <div className="sun-cfg-panel__head">
        <div>
          <h2 className="sun-cfg-panel__title">{t('groups.logo')}</h2>
          <p className="sun-cfg-panel__sub">{t('intro')}</p>
        </div>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      ) : loading ? (
        <Spinner />
      ) : (
        <div className="sun-brandform">
          <section className="sun-brandgroup">
            <div className="sun-divider">{t('groups.logo')}</div>
            <div className="sun-field">
              <label className="sun-field__label" htmlFor={logoId}>{t('fields.logo')}</label>
              <div className="sun-logopick">
                <div className="sun-logopick__preview" aria-hidden={!logoSrc}>
                  {logoSrc ? (
                    <img src={logoSrc} alt={t('logo.current')} />
                  ) : (
                    <span className="sun-logopick__empty"><Icon name="image" size={22} />{t('logo.empty')}</span>
                  )}
                </div>
                <div className="sun-logopick__actions">
                  <input
                    ref={fileRef}
                    id={logoId}
                    type="file"
                    accept="image/*"
                    className="sun-logopick__input"
                    aria-describedby={`${logoId}-hint`}
                    onChange={onLogoPicked}
                  />
                  <Btn
                    variant="secondary"
                    icon="upload"
                    busy={uploading}
                    onClick={() => fileRef.current?.click()}
                  >
                    {logoPath ? t('logo.replace') : t('logo.upload')}
                  </Btn>
                  <span id={`${logoId}-hint`} className="sun-field__hint">{t('fields.logoHint')}</span>
                </div>
              </div>
            </div>
          </section>

          <section className="sun-brandgroup">
            <div className="sun-divider">{t('groups.color')}</div>
            <div className="sun-field">
              <label className="sun-field__label" htmlFor={colorPickerId}>{t('fields.primaryColor')}</label>
              <div className="sun-colorrow">
                <input
                  type="color"
                  id={colorPickerId}
                  value={isHex(primaryColor) ? primaryColor : '#16a34a'}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="sun-colorrow__swatch"
                />
                <input
                  className="sun-input"
                  aria-label={t('fields.colorText')}
                  placeholder="#16a34a"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                />
              </div>
            </div>
          </section>

          <section className="sun-brandgroup">
            <div className="sun-divider">{t('groups.footer')}</div>
            <div className="sun-field">
              <label className="sun-field__label" htmlFor={footerId}>{t('fields.footerText')}</label>
              <textarea
                id={footerId}
                className="sun-input"
                rows={3}
                value={footerText}
                onChange={(e) => setFooterText(e.target.value)}
              />
            </div>
          </section>

          <section className="sun-brandgroup">
            <div className="sun-divider">{t('groups.serial')}</div>
            <div className="sun-field">
              <label className="sun-field__label" htmlFor={prefixId}>{t('fields.projectPrefix')}</label>
              <input
                id={prefixId}
                className="sun-input sun-input--prefix"
                maxLength={8}
                placeholder="SUN"
                value={projectPrefix}
                aria-describedby={`${prefixId}-hint`}
                onChange={(e) => setProjectPrefix(e.target.value.toUpperCase())}
              />
              <span id={`${prefixId}-hint`} className="sun-field__hint">{t('fields.prefixHint')}</span>
            </div>
          </section>

          <div className="sun-brandform__foot">
            <Btn variant="primary" icon="save" busy={saving} onClick={save}>{t('save')}</Btn>
          </div>
        </div>
      )}
    </div>
  )
}

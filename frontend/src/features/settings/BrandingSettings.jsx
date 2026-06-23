import { useEffect, useId, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Topbar, Btn, Field, Spinner, ErrorState } from '@/shared/ui'
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
  const [logoPath, setLogoPath] = useState('')
  const [primaryColor, setPrimaryColor] = useState('')
  const [footerText, setFooterText] = useState('')
  const colorPickerId = useId()
  const footerId = useId()

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
      })
      .catch((e) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [])

  async function save() {
    setSaving(true)
    try {
      await api.org.setBranding({
        logo_path: logoPath.trim() || null,
        primary_color: primaryColor.trim() || null,
        footer_text: footerText.trim() || null,
      })
      toast('success', t('saved'))
    } catch (e) {
      toast('error', t('saveError'), e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <Topbar title={t('title')} crumb={t('crumb')} />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={() => window.location.reload()} />
        ) : loading ? (
          <Spinner />
        ) : (
          <div className="sun-card" style={{ padding: 'var(--space-5)', maxWidth: 560 }}>
            <p style={{ color: 'var(--text-muted)', marginTop: 0 }}>{t('intro')}</p>
            <div className="sun-speclist">
              <Field
                label={t('fields.logoPath')}
                hint={t('fields.logoHint')}
                icon="image"
                value={logoPath}
                onChange={(e) => setLogoPath(e.target.value)}
              />
              <div className="sun-field">
                <label className="sun-field__label" htmlFor={colorPickerId}>{t('fields.primaryColor')}</label>
                <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                  <input
                    type="color"
                    id={colorPickerId}
                    value={isHex(primaryColor) ? primaryColor : '#16a34a'}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    style={{ width: 44, height: 38, padding: 0, border: 'none', background: 'none', cursor: 'pointer' }}
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
              <div>
                <Btn variant="primary" icon="save" busy={saving} onClick={save}>{t('save')}</Btn>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

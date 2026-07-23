import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Icon, IconBtn, Spinner } from '@/shared/ui'
import { api } from '@/api/client'
import { wireAssist, emitView, assistBus, getSnapshot } from './wiring'
import './assist.css'

const RECENT_ERROR_MS = 2 * 60 * 1000

export function HelpAssist() {
  const { t } = useTranslation('assist')
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [ctx, setCtx] = useState(() => getSnapshot().context)
  const [html, setHtml] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => { wireAssist() }, [])
  useEffect(() => { emitView(location.pathname) }, [location.pathname])
  useEffect(() => {
    setCtx({ ...getSnapshot().context })
    const offs = ['nav.view', 'nav.subview'].map((type) =>
      assistBus.on(type, () => setCtx({ ...getSnapshot().context })),
    )
    return () => offs.forEach((off) => off())
  }, [])

  useEffect(() => {
    if (!open) return undefined
    let alive = true
    setLoading(true)
    setError(null)
    api.help.tutorial({ view: ctx.view, subview: ctx.subview })
      .then((h) => { if (alive) setHtml(h) })
      .catch((e) => { if (alive) setError(e.message) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [open, ctx.view, ctx.subview])

  useEffect(() => {
    if (!open) return undefined
    function onKey(e) { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  function toggle() {
    const next = !open
    setOpen(next)
    assistBus.emit(next ? 'help.open' : 'help.close', { view: ctx.view, subview: ctx.subview })
  }

  const snap = getSnapshot()
  const recentError = snap.errors.length
    ? snap.errors[snap.errors.length - 1]
    : null
  const showError = recentError && Date.now() - recentError.t < RECENT_ERROR_MS

  const viewLabel = ctx.view ? t(`views.${ctx.view}`, { defaultValue: ctx.view }) : ''
  const subviewLabel = ctx.subview
    ? t(`subviews.${ctx.view}.${ctx.subview}`, { defaultValue: ctx.subview })
    : null

  return (
    <>
      <button
        type="button"
        className={`sun-assist-tab${open ? ' sun-assist-tab--open' : ''}`}
        aria-expanded={open}
        aria-controls="assist-panel"
        data-assist="assist:tab"
        onClick={toggle}
      >
        <Icon name="circle-help" size={15} />
        <span>{t('tab')}</span>
      </button>
      <aside
        id="assist-panel"
        className={`sun-assist${open ? ' sun-assist--open' : ''}`}
        aria-label={t('title')}
        aria-hidden={open ? undefined : 'true'}
        {...(open ? {} : { inert: '' })}
      >
        <div className="sun-assist__head">
          <Icon name="circle-help" size={18} color="var(--green-600)" />
          <h3>{t('title')}</h3>
          <IconBtn icon="x" label={t('close')} size="sm" onClick={toggle} />
        </div>
        <div className="sun-assist__context">
          <span className="sun-assist__crumb">
            <Icon name="map-pin" size={13} />
            {t('youAreIn')} <strong>{viewLabel}</strong>
            {subviewLabel && <> · {subviewLabel}</>}
          </span>
        </div>
        {showError && (
          <div className="sun-assist__alert">
            <Icon name="alert-triangle" size={14} />
            <span>{t('recentError')} <code>{recentError.message}</code></span>
          </div>
        )}
        <div className="sun-assist__body">
          {loading ? (
            <Spinner label={t('loading')} />
          ) : error ? (
            <div className="sun-inline-note sun-inline-note--danger">
              <Icon name="alert-circle" size={14} />{error}
            </div>
          ) : html ? (
            <div dangerouslySetInnerHTML={{ __html: html }} />
          ) : null}
        </div>
        <div className="sun-assist__foot">
          <Icon name="sparkles" size={13} />
          <span>{t('agentSoon')}</span>
        </div>
      </aside>
    </>
  )
}

import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Icon, IconBtn, Spinner, ConfirmDialog } from '@/shared/ui'
import { api } from '@/api/client'
import { getUnsavedGuard } from '@/shared/unsavedGuard'
import { wireAssist, emitView, assistBus, getSnapshot } from './wiring'
import { solutionFor } from './solutions'
import './assist.css'

const RECENT_ERROR_MS = 2 * 60 * 1000

export function HelpAssist() {
  const { t } = useTranslation('assist')
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [ctx, setCtx] = useState(() => getSnapshot().context)
  const [html, setHtml] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pendingHref, setPendingHref] = useState(null)
  const [pulse, setPulse] = useState(false)

  function go(href) {
    setPendingHref(null)
    navigate(href)
  }

  function navigateSafe(href) {
    assistBus.emit('help.link', { href, view: ctx.view, subview: ctx.subview })
    const guard = getUnsavedGuard()
    if (guard && guard.isDirty()) setPendingHref(href)
    else go(href)
  }

  function onBodyClick(e) {
    const a = e.target instanceof Element ? e.target.closest('a[href^="/app"]') : null
    if (!a) return
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return
    e.preventDefault()
    navigateSafe(a.getAttribute('href'))
  }

  async function saveAndGo() {
    const guard = getUnsavedGuard()
    const href = pendingHref
    if (!guard) { go(href); return }
    const ok = await guard.save()
    if (ok) go(href)
  }

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

  useEffect(() => assistBus.on('assist.frustration', () => {
    setPulse(true)
  }), [])

  useEffect(() => {
    if (!pulse) return undefined
    if (open) { setPulse(false); return undefined }
    const timer = setTimeout(() => setPulse(false), 6000)
    return () => clearTimeout(timer)
  }, [pulse, open])

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
  const fix = showError ? solutionFor(recentError) : null

  const viewLabel = ctx.view ? t(`views.${ctx.view}`, { defaultValue: ctx.view }) : ''
  const subviewLabel = ctx.subview
    ? t(`subviews.${ctx.view}.${ctx.subview}`, { defaultValue: ctx.subview })
    : null

  return (
    <>
      <button
        type="button"
        className={`sun-assist-tab${open ? ' sun-assist-tab--open' : ''}${pulse ? ' sun-assist-tab--pulse' : ''}`}
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
            <span>
              {t('recentError')} <code>{recentError.message}</code>
              {fix && (
                <button type="button" className="sun-assist__fix" onClick={() => navigateSafe(fix.href)}>
                  <Icon name="arrow-right" size={12} />
                  {t('fixIn', { view: t(`views.${fix.view}`) })}
                </button>
              )}
            </span>
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
            /* eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events */
            <div onClick={onBodyClick} dangerouslySetInnerHTML={{ __html: html }} />
          ) : null}
        </div>
        <div className="sun-assist__foot">
          <Icon name="sparkles" size={13} />
          <span>{t('agentSoon')}</span>
        </div>
      </aside>
      <ConfirmDialog
        open={Boolean(pendingHref)}
        title={t('unsaved.title')}
        description={t('unsaved.desc')}
        onClose={() => setPendingHref(null)}
        actions={[
          { label: t('unsaved.cancel'), variant: 'ghost', onClick: () => setPendingHref(null) },
          { label: t('unsaved.discard'), variant: 'secondary', icon: 'arrow-right', onClick: () => go(pendingHref) },
          { label: t('unsaved.saveAndGo'), variant: 'primary', icon: 'save', onClick: saveAndGo },
        ]}
      />
    </>
  )
}

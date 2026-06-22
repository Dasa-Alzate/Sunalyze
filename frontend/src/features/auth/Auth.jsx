import { useState, useEffect, useId } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Btn, Icon, Field, Spinner } from '@/shared/ui'
import { useTransition } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { toast } from '@/services/toast'
import { messageForError } from '@/services/i18n'
import { api } from '@/api/client'

const PATHS = { landing: '/', login: '/login', signup: '/signup', forgot: '/recuperar', app: '/app', reset: '/reset-password' }

function pathOf(key) {
  return PATHS[key] || key
}

function useGo() {
  const { navigate } = useTransition()
  return (key) => navigate(pathOf(key))
}

function TopBrand({ go }) {
  return (
    <a className="auth__topbrand" href={pathOf('landing')} onClick={(e) => { e.preventDefault(); go('landing') }}>
      <span className="mark"><Icon name="sun" size={16} strokeWidth={2.4} /></span>Sunalyze
    </a>
  )
}

function Shell({ go, children }) {
  return (
    <div className="auth">
      <div className="auth__bg" />
      <div className="auth__grid-lines" />
      <TopBrand go={go} />
      {children}
    </div>
  )
}

function PasswordField({ label, hint, autoComplete = 'current-password', value, onChange }) {
  const { t } = useTranslation('auth')
  const [show, setShow] = useState(false)
  const fieldId = useId()
  const hintId = `${fieldId}-hint`
  return (
    <div className="sun-field">
      <label className="sun-field__label" htmlFor={fieldId}>{label || t('password.label')}</label>
      <div className="auth-pw">
        <input id={fieldId} className="sun-input" type={show ? 'text' : 'password'} autoComplete={autoComplete}
          placeholder="••••••••" style={{ paddingRight: 38 }} value={value} onChange={onChange}
          aria-describedby={hint ? hintId : undefined} />
        <button type="button" className="sun-iconbtn sun-iconbtn--sm auth-reveal" aria-label={show ? t('password.hide') : t('password.show')}
          onClick={() => setShow((s) => !s)}><Icon name={show ? 'eye-off' : 'eye'} size={16} /></button>
      </div>
      {hint && <span id={hintId} className="sun-field__hint">{hint}</span>}
    </div>
  )
}

function SSO() {
  const { t } = useTranslation('auth')
  const onSso = () => toast('info', t('sso.unavailableTitle'), t('sso.unavailableDesc'))
  return (
    <>
      <div className="auth-divider">{t('sso.divider')}</div>
      <div className="auth-sso">
        <Btn variant="secondary" size="lg" block icon="building-2" type="button" onClick={onSso}>{t('sso.microsoft')}</Btn>
        <Btn variant="secondary" size="lg" block icon="mail" type="button" onClick={onSso}>{t('sso.google')}</Btn>
      </div>
    </>
  )
}

export function Login() {
  const { t } = useTranslation('auth')
  const go = useGo()
  const [params] = useSearchParams()
  const next = params.get('next')
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      await login({ email, password, remember })
      toast('success', t('login.successTitle'), t('login.successDesc'))
      go(next || 'app')
    } catch (err) {
      toast('error', t('login.errorTitle'), messageForError(err, t))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>{t('login.title')}</h1>
            <p>{t('login.subtitle')}</p>
          </div>
          <form className="auth-form" onSubmit={submit}>
            <Field label={t('login.email')} icon="mail" type="email" autoComplete="username" placeholder={t('login.emailPlaceholder')} value={email} onChange={(e) => setEmail(e.target.value)} />
            <PasswordField value={password} onChange={(e) => setPassword(e.target.value)} />
            <div className="auth-aux">
              <label className="sun-check"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /><span className="sun-check__box"><Icon name="check" size={13} /></span><span>{t('login.remember')}</span></label>
              <a href={pathOf('forgot')} onClick={(e) => { e.preventDefault(); go('forgot') }}>{t('login.forgot')}</a>
            </div>
            <Btn variant="primary" size="lg" block type="submit" iconRight="arrow-right" disabled={busy} data-busy={busy}>{busy ? t('login.submitting') : t('login.submit')}</Btn>
            <SSO />
          </form>
          <div className="auth-foot">{t('login.noAccount')} <a href={pathOf('signup')} onClick={(e) => { e.preventDefault(); go('signup') }}>{t('login.createFree')}</a></div>
        </div>
        <p className="auth-legal">{t('legal.prefix')} <a href="/legal/terminos" onClick={(e) => { e.preventDefault(); go('/legal/terminos') }}>{t('legal.terms')}</a> {t('legal.and')} <a href="/legal/privacidad" onClick={(e) => { e.preventDefault(); go('/legal/privacidad') }}>{t('legal.privacy')}</a> {t('legal.suffix')}</p>
      </div>
    </Shell>
  )
}

export function Signup() {
  const { t } = useTranslation('auth')
  const go = useGo()
  const { register } = useAuth()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', company: '', password: '' })
  const [score, setScore] = useState(0)
  const [accepted, setAccepted] = useState(false)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  function onPassword(e) {
    const v = e.target.value
    setForm((f) => ({ ...f, password: v }))
    let s = 0
    if (v.length >= 8) s++
    if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++
    if (/\d/.test(v)) s++
    if (/[^A-Za-z0-9]/.test(v)) s++
    setScore(s)
  }

  async function submit(e) {
    e.preventDefault()
    if (!accepted) { toast('warning', t('signup.acceptWarnTitle'), t('signup.acceptWarnDesc')); return }
    setBusy(true)
    try {
      await register(form)
      toast('success', t('signup.successTitle'), t('signup.successDesc'))
      go('app')
    } catch (err) {
      toast('error', t('signup.errorTitle'), messageForError(err, t))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>{t('signup.title')}</h1>
            <p>{t('signup.subtitle')}</p>
          </div>
          <form className="auth-form" onSubmit={submit}>
            <div className="auth-form__row">
              <Field label={t('signup.firstName')} placeholder="María" autoComplete="given-name" value={form.first_name} onChange={set('first_name')} />
              <Field label={t('signup.lastName')} placeholder="Ruiz" autoComplete="family-name" value={form.last_name} onChange={set('last_name')} />
            </div>
            <Field label={t('signup.email')} icon="mail" type="email" autoComplete="username" placeholder={t('signup.emailPlaceholder')} value={form.email} onChange={set('email')} />
            <Field label={t('signup.company')} icon="building-2" placeholder={t('signup.companyPlaceholder')} value={form.company} onChange={set('company')} />
            <div>
              <PasswordField label={t('password.label')} autoComplete="new-password" value={form.password} onChange={onPassword} hint={t('password.hint')} />
              <div className="auth-pwhint">
                {[0, 1, 2, 3].map((i) => <span key={i} className={`bar${i < score ? ' on' : ''}`} />)}
              </div>
            </div>
            <label className="sun-check" style={{ alignItems: 'flex-start', gap: 8 }}>
              <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} /><span className="sun-check__box"><Icon name="check" size={13} /></span>
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>{t('signup.accept')}</span>
            </label>
            <Btn variant="primary" size="lg" block type="submit" iconRight="arrow-right" disabled={busy} data-busy={busy}>{busy ? t('signup.submitting') : t('signup.submit')}</Btn>
            <SSO />
          </form>
          <div className="auth-foot">{t('signup.haveAccount')} <a href={pathOf('login')} onClick={(e) => { e.preventDefault(); go('login') }}>{t('login.title')}</a></div>
        </div>
      </div>
    </Shell>
  )
}

export function ForgotPassword() {
  const { t } = useTranslation('auth')
  const go = useGo()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [devLink, setDevLink] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const r = await api.auth.forgotPassword({ email })
      setDevLink(r.reset_link || null)
      setSent(true)
    } catch (err) {
      toast('error', t('forgot.errorTitle'), messageForError(err, t))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          {!sent ? (
            <>
              <div className="auth-card__head">
                <h1>{t('forgot.title')}</h1>
                <p>{t('forgot.subtitle')}</p>
              </div>
              <form className="auth-form" onSubmit={submit}>
                <Field label={t('login.email')} icon="mail" type="email" autoComplete="username" placeholder={t('login.emailPlaceholder')} value={email} onChange={(e) => setEmail(e.target.value)} />
                <Btn variant="primary" size="lg" block type="submit" iconRight="send" disabled={busy} data-busy={busy}>{busy ? t('forgot.submitting') : t('forgot.submit')}</Btn>
              </form>
              <div className="auth-foot"><a href={pathOf('login')} onClick={(e) => { e.preventDefault(); go('login') }}><Icon name="arrow-left" size={14} style={{ marginRight: 5, verticalAlign: '-2px' }} />{t('forgot.backToLogin')}</a></div>
            </>
          ) : (
            <div className="auth-success">
              <div className="auth-success__icon"><Icon name="mail-check" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>{t('forgot.sentTitle')}</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>{t('forgot.sentDesc')}</p>
              {devLink && (
                <a href={devLink} className="sun-inline-note sun-inline-note--info" style={{ textDecoration: 'none', wordBreak: 'break-all' }}>
                  <Icon name="info" size={14} /> {t('forgot.devLink')}
                </a>
              )}
              <Btn variant="secondary" size="md" block icon="arrow-left" onClick={() => go('login')}>{t('forgot.backToLogin')}</Btn>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}

export function ResetPassword() {
  const { t } = useTranslation('auth')
  const go = useGo()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      await api.auth.resetPassword({ token, password })
      toast('success', t('reset.successTitle'), t('reset.successDesc'))
      go('login')
    } catch (err) {
      toast('error', t('reset.errorTitle'), messageForError(err, t))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>{t('reset.title')}</h1>
            <p>{t('reset.subtitle')}</p>
          </div>
          {!token ? (
            <div className="sun-inline-note sun-inline-note--danger"><Icon name="alert-triangle" size={14} /> {t('reset.noToken')}</div>
          ) : (
            <form className="auth-form" onSubmit={submit}>
              <PasswordField label={t('reset.newPassword')} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} hint={t('password.hint')} />
              <Btn variant="primary" size="lg" block type="submit" iconRight="check" disabled={busy} data-busy={busy}>{busy ? t('reset.submitting') : t('reset.submit')}</Btn>
            </form>
          )}
          <div className="auth-foot"><a href={pathOf('login')} onClick={(e) => { e.preventDefault(); go('login') }}>{t('forgot.backToLogin')}</a></div>
        </div>
      </div>
    </Shell>
  )
}

export function VerifyEmail() {
  const { t } = useTranslation('auth')
  const go = useGo()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [state, setState] = useState('loading')

  useEffect(() => {
    if (!token) { setState('error'); return }
    let alive = true
    api.auth.verifyEmail({ token })
      .then(() => alive && setState('ok'))
      .catch(() => alive && setState('error'))
    return () => { alive = false }
  }, [token])

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          {state === 'loading' && <Spinner label={t('verify.loading')} />}
          {state === 'ok' && (
            <div className="auth-success">
              <div className="auth-success__icon"><Icon name="mail-check" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>{t('verify.okTitle')}</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>{t('verify.okDesc')}</p>
              <Btn variant="primary" size="md" block iconRight="arrow-right" onClick={() => go('app')}>{t('verify.goApp')}</Btn>
            </div>
          )}
          {state === 'error' && (
            <div className="auth-success">
              <div className="auth-success__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}><Icon name="alert-triangle" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>{t('verify.errorTitle')}</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>{t('verify.errorDesc')}</p>
              <Btn variant="secondary" size="md" block icon="arrow-left" onClick={() => go('login')}>{t('forgot.backToLogin')}</Btn>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}

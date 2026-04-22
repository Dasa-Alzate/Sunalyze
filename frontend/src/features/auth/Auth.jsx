import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Btn, Icon, Field, Spinner } from '@/shared/ui'
import { useTransition } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { toast } from '@/services/toast'
import { api } from '@/api/client'

const PATHS = { landing: '/', login: '/login', signup: '/signup', forgot: '/recuperar', app: '/app', reset: '/reset-password' }

function useGo() {
  const { navigate } = useTransition()
  return (key) => navigate(PATHS[key] || key)
}

function TopBrand({ go }) {
  return (
    <a className="auth__topbrand" href="#" onClick={(e) => { e.preventDefault(); go('landing') }}>
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

function PasswordField({ label = 'Contraseña', hint, autoComplete = 'current-password', value, onChange }) {
  const [show, setShow] = useState(false)
  return (
    <div className="sun-field">
      <label className="sun-field__label">{label}</label>
      <div className="auth-pw">
        <input className="sun-input" type={show ? 'text' : 'password'} autoComplete={autoComplete}
          placeholder="••••••••" style={{ paddingRight: 38 }} value={value} onChange={onChange} />
        <button type="button" className="sun-iconbtn sun-iconbtn--sm auth-reveal" aria-label={show ? 'Ocultar' : 'Mostrar'}
          onClick={() => setShow((s) => !s)}><Icon name={show ? 'eye-off' : 'eye'} size={16} /></button>
      </div>
      {hint && <span className="sun-field__hint">{hint}</span>}
    </div>
  )
}

function SSO() {
  return (
    <>
      <div className="auth-divider">o continúa con</div>
      <div className="auth-sso">
        <Btn variant="secondary" size="lg" block icon="building-2" type="button" onClick={() => toast('info', 'SSO no disponible', 'Pendiente de configurar el proveedor')}>Cuenta de Microsoft</Btn>
        <Btn variant="secondary" size="lg" block icon="mail" type="button" onClick={() => toast('info', 'SSO no disponible', 'Pendiente de configurar el proveedor')}>Google Workspace</Btn>
      </div>
    </>
  )
}

function authError(e) {
  if (e?.data?.details?.length) return e.data.details.map((d) => d.msg).join(' · ')
  return e?.message || 'Ha ocurrido un error'
}

export function Login() {
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
      toast('success', 'Sesión iniciada', 'Redirigiendo a tus proyectos…')
      go(next || 'app')
    } catch (err) {
      toast('error', 'No se pudo iniciar sesión', authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>Iniciar sesión</h1>
            <p>Bienvenido de nuevo. Accede a tus proyectos.</p>
          </div>
          <form className="auth-form" onSubmit={submit}>
            <Field label="Correo electrónico" icon="mail" type="email" autoComplete="username" placeholder="tu@empresa.es" value={email} onChange={(e) => setEmail(e.target.value)} />
            <PasswordField value={password} onChange={(e) => setPassword(e.target.value)} />
            <div className="auth-aux">
              <label className="sun-check"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /><span className="sun-check__box"><Icon name="check" size={13} /></span><span>Mantener sesión</span></label>
              <a href="#" onClick={(e) => { e.preventDefault(); go('forgot') }}>¿Olvidaste tu contraseña?</a>
            </div>
            <Btn variant="primary" size="lg" block type="submit" iconRight="arrow-right" disabled={busy} data-busy={busy}>{busy ? 'Entrando…' : 'Iniciar sesión'}</Btn>
            <SSO />
          </form>
          <div className="auth-foot">¿No tienes cuenta? <a href="#" onClick={(e) => { e.preventDefault(); go('signup') }}>Crear cuenta gratis</a></div>
        </div>
        <p className="auth-legal">Al continuar aceptas las <a href="#">Condiciones</a> y la <a href="#">Política de privacidad</a> de Sunalyze.</p>
      </div>
    </Shell>
  )
}

export function Signup() {
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
    if (!accepted) { toast('warning', 'Acepta las condiciones', 'Debes aceptar las condiciones para continuar'); return }
    setBusy(true)
    try {
      await register(form)
      toast('success', 'Cuenta creada', 'Te damos la bienvenida a Sunalyze.')
      go('app')
    } catch (err) {
      toast('error', 'No se pudo crear la cuenta', authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>Crear cuenta</h1>
            <p>14 días gratis. Sin tarjeta de crédito.</p>
          </div>
          <form className="auth-form" onSubmit={submit}>
            <div className="auth-form__row">
              <Field label="Nombre" placeholder="María" autoComplete="given-name" value={form.first_name} onChange={set('first_name')} />
              <Field label="Apellidos" placeholder="Ruiz" autoComplete="family-name" value={form.last_name} onChange={set('last_name')} />
            </div>
            <Field label="Correo de trabajo" icon="mail" type="email" autoComplete="username" placeholder="maria@empresa.es" value={form.email} onChange={set('email')} />
            <Field label="Empresa / instalador" icon="building-2" placeholder="Solar Levante S.L. (opcional)" value={form.company} onChange={set('company')} />
            <div>
              <PasswordField label="Contraseña" autoComplete="new-password" value={form.password} onChange={onPassword} hint="Mínimo 8 caracteres, con letras y un número." />
              <div className="auth-pwhint">
                {[0, 1, 2, 3].map((i) => <span key={i} className={`bar${i < score ? ' on' : ''}`} />)}
              </div>
            </div>
            <label className="sun-check" style={{ alignItems: 'flex-start', gap: 8 }}>
              <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} /><span className="sun-check__box"><Icon name="check" size={13} /></span>
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>Acepto las Condiciones de uso y la Política de privacidad.</span>
            </label>
            <Btn variant="primary" size="lg" block type="submit" iconRight="arrow-right" disabled={busy} data-busy={busy}>{busy ? 'Creando…' : 'Crear cuenta'}</Btn>
            <SSO />
          </form>
          <div className="auth-foot">¿Ya tienes cuenta? <a href="#" onClick={(e) => { e.preventDefault(); go('login') }}>Iniciar sesión</a></div>
        </div>
      </div>
    </Shell>
  )
}

export function ForgotPassword() {
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
      toast('error', 'No se pudo enviar', authError(err))
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
                <h1>Recuperar contraseña</h1>
                <p>Te enviaremos un enlace para restablecerla.</p>
              </div>
              <form className="auth-form" onSubmit={submit}>
                <Field label="Correo electrónico" icon="mail" type="email" autoComplete="username" placeholder="tu@empresa.es" value={email} onChange={(e) => setEmail(e.target.value)} />
                <Btn variant="primary" size="lg" block type="submit" iconRight="send" disabled={busy} data-busy={busy}>{busy ? 'Enviando…' : 'Enviar enlace'}</Btn>
              </form>
              <div className="auth-foot"><a href="#" onClick={(e) => { e.preventDefault(); go('login') }}><Icon name="arrow-left" size={14} style={{ marginRight: 5, verticalAlign: '-2px' }} />Volver a iniciar sesión</a></div>
            </>
          ) : (
            <div className="auth-success">
              <div className="auth-success__icon"><Icon name="mail-check" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>Revisa tu correo</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>Si existe una cuenta con ese correo, hemos enviado un enlace. Caduca en 60 minutos.</p>
              {devLink && (
                <a href={devLink} className="sun-inline-note sun-inline-note--info" style={{ textDecoration: 'none', wordBreak: 'break-all' }}>
                  <Icon name="info" size={14} /> Enlace de desarrollo (SMTP no configurado): abrir restablecimiento
                </a>
              )}
              <Btn variant="secondary" size="md" block icon="arrow-left" onClick={() => go('login')}>Volver a iniciar sesión</Btn>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}

export function ResetPassword() {
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
      toast('success', 'Contraseña actualizada', 'Ya puedes iniciar sesión.')
      go('login')
    } catch (err) {
      toast('error', 'No se pudo restablecer', authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell go={go}>
      <div className="web-view">
        <div className="auth-card">
          <div className="auth-card__head">
            <h1>Nueva contraseña</h1>
            <p>Elige una contraseña para tu cuenta.</p>
          </div>
          {!token ? (
            <div className="sun-inline-note sun-inline-note--danger"><Icon name="alert-triangle" size={14} /> Falta el token del enlace. Solicita un nuevo correo de recuperación.</div>
          ) : (
            <form className="auth-form" onSubmit={submit}>
              <PasswordField label="Nueva contraseña" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} hint="Mínimo 8 caracteres, con letras y un número." />
              <Btn variant="primary" size="lg" block type="submit" iconRight="check" disabled={busy} data-busy={busy}>{busy ? 'Guardando…' : 'Guardar contraseña'}</Btn>
            </form>
          )}
          <div className="auth-foot"><a href="#" onClick={(e) => { e.preventDefault(); go('login') }}>Volver a iniciar sesión</a></div>
        </div>
      </div>
    </Shell>
  )
}

export function VerifyEmail() {
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
          {state === 'loading' && <Spinner label="Verificando tu correo…" />}
          {state === 'ok' && (
            <div className="auth-success">
              <div className="auth-success__icon"><Icon name="mail-check" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>Correo verificado</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>Tu cuenta está confirmada.</p>
              <Btn variant="primary" size="md" block iconRight="arrow-right" onClick={() => go('app')}>Ir a la aplicación</Btn>
            </div>
          )}
          {state === 'error' && (
            <div className="auth-success">
              <div className="auth-success__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}><Icon name="alert-triangle" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>Enlace no válido</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>El enlace de verificación ha caducado o no es válido.</p>
              <Btn variant="secondary" size="md" block icon="arrow-left" onClick={() => go('login')}>Volver a iniciar sesión</Btn>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}

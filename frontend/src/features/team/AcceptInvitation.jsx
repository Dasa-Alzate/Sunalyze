import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Btn, Icon, Spinner } from '@/shared/ui'
import { useTransition } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { toast } from '@/services/toast'
import { api } from '@/api/client'

const ROLE_LABEL = { owner: 'Propietario', admin: 'Administrador', member: 'Miembro' }

export default function AcceptInvitation() {
  const { navigate } = useTransition()
  const { user, loading, refresh } = useAuth()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [state, setState] = useState('loading')
  const [invitation, setInvitation] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (loading) return
    if (!token) { setState('error'); return }
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(`/invitacion?token=${token}`)}`)
      return
    }
    let alive = true
    api.invitations.get(token)
      .then((inv) => {
        if (!alive) return
        setInvitation(inv)
        setState(inv.status === 'pending' && !inv.expired ? 'ready' : 'invalid')
      })
      .catch(() => alive && setState('error'))
    return () => { alive = false }
  }, [token, user, loading])

  async function join() {
    setBusy(true)
    try {
      await api.invitations.accept(token)
      await refresh()
      toast('success', 'Te has unido al equipo', `Ahora colaboras en ${invitation?.org_nombre || 'el workspace'}.`)
      navigate('/app')
    } catch (e) {
      toast('error', 'No se pudo aceptar', e.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth">
      <div className="auth__bg" />
      <div className="auth__grid-lines" />
      <a className="auth__topbrand" href="/" onClick={(e) => { e.preventDefault(); navigate('/') }}>
        <span className="mark"><Icon name="sun" size={16} strokeWidth={2.4} /></span>Sunalyze
      </a>
      <div className="web-view">
        <div className="auth-card">
          {state === 'loading' && <Spinner label="Cargando invitación…" />}
          {state === 'ready' && (
            <>
              <div className="auth-card__head">
                <h1>Unirte a {invitation.org_nombre}</h1>
                <p>{invitation.inviter || 'Un compañero'} te ha invitado como {ROLE_LABEL[invitation.role]?.toLowerCase() || invitation.role}.</p>
              </div>
              <div className="sun-inline-note sun-inline-note--info" style={{ marginBottom: 'var(--space-4)' }}>
                <Icon name="info" size={14} /> Invitación para {invitation.email}. Te unirás con la sesión actual.
              </div>
              <Btn variant="primary" size="lg" block iconRight="arrow-right" disabled={busy} data-busy={busy} onClick={join}>
                {busy ? 'Uniéndote…' : 'Unirme al equipo'}
              </Btn>
              <div className="auth-foot"><a href="/app" onClick={(e) => { e.preventDefault(); navigate('/app') }}>Ahora no</a></div>
            </>
          )}
          {state === 'invalid' && (
            <div className="auth-success">
              <div className="auth-success__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}><Icon name="alert-triangle" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>Invitación no disponible</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>Esta invitación ha caducado, fue revocada o ya se aceptó.</p>
              <Btn variant="secondary" size="md" block icon="arrow-right" onClick={() => navigate('/app')}>Ir a la aplicación</Btn>
            </div>
          )}
          {state === 'error' && (
            <div className="auth-success">
              <div className="auth-success__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}><Icon name="alert-triangle" size={28} /></div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)', margin: 0, color: 'var(--text-strong)' }}>Enlace no válido</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-base)', margin: 0 }}>Falta el token o la invitación no existe.</p>
              <Btn variant="secondary" size="md" block icon="arrow-right" onClick={() => navigate('/app')}>Ir a la aplicación</Btn>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

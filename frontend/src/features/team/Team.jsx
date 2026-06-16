import { useEffect, useState } from 'react'
import { Topbar, Btn, IconBtn, Icon, Badge, Field, SelectField, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { useAuth } from '@/services/auth'

const ROLE_LABEL = { owner: 'Propietario', admin: 'Administrador', member: 'Miembro' }
const ROLE_TONE = { owner: 'brand', admin: 'info', member: 'neutral' }

function initials(name) {
  if (!name) return 'U'
  return name.trim().split(/\s+/).slice(0, 2).map((s) => s[0]?.toUpperCase()).join('') || 'U'
}

export default function Team() {
  const { user, can, refresh } = useAuth()
  const canInvite = can('member:invite')
  const canManage = can('member:manage')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [inviteOpen, setInviteOpen] = useState(false)

  function load() {
    setError(null)
    api.members.list().then(setData).catch((e) => setError(e.message))
  }

  useEffect(load, [])

  const org = data?.org
  const isPersonal = org?.type === 'PERSONAL'
  const members = data?.members || []
  const invitations = data?.invitations || []
  const ownerCount = members.filter((m) => m.role === 'owner').length

  async function changeRole(m, role) {
    if (role === m.role) return
    try {
      await api.members.changeRole(m.user_id, role)
      toast('success', 'Rol actualizado', `${m.full_name || m.email} ahora es ${ROLE_LABEL[role].toLowerCase()}`)
      load()
      if (m.user_id === user?.id) refresh()
    } catch (e) {
      toast('error', 'No se pudo cambiar el rol', e.message)
    }
  }

  async function removeMember(m) {
    if (!window.confirm(`¿Expulsar a ${m.full_name || m.email}? Los proyectos del workspace se conservan.`)) return
    try {
      await api.members.remove(m.user_id)
      toast('success', 'Miembro expulsado')
      load()
    } catch (e) {
      toast('error', 'No se pudo expulsar', e.message)
    }
  }

  async function revoke(inv) {
    if (!window.confirm(`¿Revocar la invitación a ${inv.email}?`)) return
    try {
      await api.invitations.revoke(inv.id)
      toast('success', 'Invitación revocada')
      load()
    } catch (e) {
      toast('error', 'No se pudo revocar', e.message)
    }
  }

  async function invite(values) {
    const email = values.email.trim()
    if (!email) { toast('error', 'Falta el correo'); return }
    try {
      const res = await api.invitations.create({ email, role: values.role })
      if (res.accept_link) {
        toast('success', 'Invitación enviada', 'Enlace de desarrollo copiado abajo.')
      } else {
        toast('success', 'Invitación enviada', `Hemos avisado a ${email}.`)
      }
      setInviteOpen(false)
      load()
    } catch (e) {
      toast('error', 'No se pudo invitar', e.message)
    }
  }

  function canRemove(m) {
    if (!canManage) return false
    if (m.role === 'owner' && ownerCount <= 1) return false
    return true
  }

  function roleOptions(m) {
    const opts = [
      { value: 'member', label: ROLE_LABEL.member },
      { value: 'admin', label: ROLE_LABEL.admin },
      { value: 'owner', label: ROLE_LABEL.owner },
    ]
    if (m.role === 'owner' && ownerCount <= 1) {
      return opts.filter((o) => o.value === 'owner')
    }
    return opts
  }

  return (
    <>
      <Topbar title="Equipo" crumb={org?.nombre || 'Workspace'} />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : data === null ? (
          <Spinner label="Cargando equipo…" />
        ) : isPersonal ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="users" size={26} /></div>
            <div className="sun-empty__title">Espacio personal</div>
            <div className="sun-empty__desc">Los espacios personales son de un solo asiento. Crea un espacio de empresa para invitar a tu equipo.</div>
          </div>
        ) : (
          <>
            <div className="sun-toolbar">
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                {members.length} de {org?.seats || members.length} asientos · {invitations.length} pendientes
              </span>
              {canInvite && (
                <div style={{ marginLeft: 'auto' }}>
                  <Btn variant="primary" icon="user-plus" onClick={() => setInviteOpen(true)}>Invitar persona</Btn>
                </div>
              )}
            </div>

            <div className="sun-card" style={{ overflow: 'hidden' }}>
              <table className="sun-table">
                <thead>
                  <tr>
                    <th>Miembro</th>
                    <th>Correo</th>
                    <th>Rol</th>
                    <th style={{ width: 80 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.membership_id}>
                      <td className="sun-table__name">
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                          <span className="sun-avatar">{initials(m.full_name)}</span>
                          {m.full_name || '—'}{m.user_id === user?.id ? ' (tú)' : ''}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>{m.email}</td>
                      <td>
                        {canManage ? (
                          <SelectField
                            value={m.role}
                            options={roleOptions(m)}
                            onChange={(e) => changeRole(m, e.target.value)}
                          />
                        ) : (
                          <Badge tone={ROLE_TONE[m.role]} icon={m.role === 'owner' ? 'crown' : 'user'}>{ROLE_LABEL[m.role]}</Badge>
                        )}
                      </td>
                      <td>
                        {canRemove(m) ? (
                          <IconBtn icon="user-minus" label="Expulsar" size="sm" onClick={() => removeMember(m)} />
                        ) : (
                          <span style={{ color: 'var(--text-subtle)', display: 'inline-flex' }} title="Acción no disponible">
                            <Icon name="lock" size={14} />
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="sun-divider" style={{ marginTop: 'var(--space-6)' }}>Invitaciones pendientes · {invitations.length}</div>
            {invitations.length === 0 ? (
              <div className="sun-inline-note sun-inline-note--info">
                <Icon name="info" size={14} /> No hay invitaciones pendientes.
              </div>
            ) : (
              <div className="sun-card" style={{ overflow: 'hidden' }}>
                <table className="sun-table">
                  <thead>
                    <tr>
                      <th>Correo</th>
                      <th>Rol</th>
                      <th>Invitado por</th>
                      <th style={{ width: 80 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.map((inv) => (
                      <tr key={inv.id}>
                        <td className="sun-table__name">{inv.email}</td>
                        <td><Badge tone={ROLE_TONE[inv.role]} icon="user">{ROLE_LABEL[inv.role]}</Badge></td>
                        <td style={{ color: 'var(--text-muted)' }}>{inv.invited_by || '—'}</td>
                        <td>
                          {canInvite ? (
                            <IconBtn icon="x" label="Revocar" size="sm" onClick={() => revoke(inv)} />
                          ) : (
                            <span style={{ color: 'var(--text-subtle)', display: 'inline-flex' }}><Icon name="lock" size={14} /></span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {inviteOpen && <InviteDrawer onClose={() => setInviteOpen(false)} onSave={invite} />}
      </div>
    </>
  )
}

function InviteDrawer({ onClose, onSave }) {
  const [values, setValues] = useState({ email: '', role: 'member' })
  const set = (k) => (e) => setValues((s) => ({ ...s, [k]: e.target.value }))
  return (
    <div className="sun-scrim" onClick={(e) => { if (e.target.classList.contains('sun-scrim')) onClose() }}>
      <div className="sun-drawer">
        <div className="sun-drawer__head">
          <h3>Invitar persona</h3>
          <IconBtn icon="x" label="Cerrar" onClick={onClose} />
        </div>
        <div className="sun-drawer__body">
          <Field label="Correo electrónico" required type="email" icon="mail" placeholder="persona@empresa.es" value={values.email} onChange={set('email')} />
          <SelectField
            label="Rol"
            value={values.role}
            onChange={set('role')}
            options={[
              { value: 'member', label: 'Miembro · diseña proyectos' },
              { value: 'admin', label: 'Administrador · gestiona equipo y catálogos' },
            ]}
          />
        </div>
        <div className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onClose}>Cancelar</Btn>
          <Btn variant="primary" icon="send" onClick={() => onSave(values)}>Enviar invitación</Btn>
        </div>
      </div>
    </div>
  )
}

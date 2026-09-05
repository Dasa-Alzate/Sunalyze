import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Icon, IconBtn } from '@/shared/ui'
import { LanguageSwitcher } from '@/shared/LanguageSwitcher'
import { ThemeToggle } from '@/shared/ThemeToggle'
import { TransitionLink, useTransition } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { useCommands, isMac, formatShortcut } from '@/services/actions'
import { toast } from '@/services/toast'
import NotificationBell from '@/features/notifications/NotificationBell'
import WorkspaceSwitcher from '@/app/WorkspaceSwitcher'
import { HelpAssist } from '@/services/assist'

const NAV_GROUPS = [
  [
    { to: '/app', key: 'resumen', icon: 'layout-dashboard', end: true },
    { to: '/app/proyectos', key: 'proyectos', icon: 'folder' },
    { to: '/app/diseno', key: 'diseno', icon: 'sliders-horizontal' },
    { to: '/app/equipos', key: 'equipos', icon: 'package' },
    { to: '/app/memoria', key: 'memoria', icon: 'file-text' },
  ],
  [
    { to: '/app/plantillas', key: 'plantillas', icon: 'layout-template', flag: 'templates' },
    { to: '/app/finanzas', key: 'finanzas', icon: 'calculator', flag: 'finance' },
    { to: '/app/posventa', key: 'posventa', icon: 'plug-zap', flag: 'posventa' },
    { to: '/app/equipo', key: 'equipo', icon: 'users', business: true },
  ],
  [
    { to: '/app/actividad', key: 'actividad', icon: 'activity', perm: 'audit:view' },
    { to: '/app/modulos', key: 'modulos', icon: 'store' },
    { to: '/app/papelera', key: 'papelera', icon: 'trash-2', perm: 'project:delete' },
    { to: '/app/configuracion', key: 'configuracion', icon: 'settings', perm: 'org:manage' },
  ],
]

const NAV = NAV_GROUPS.flat()

function initials(name) {
  if (!name) return 'U'
  return name.trim().split(/\s+/).slice(0, 2).map((s) => s[0]?.toUpperCase()).join('') || 'U'
}

function Sidebar() {
  const { t } = useTranslation('nav')
  const { user, org, logout, isPlatformAdmin, flag, can } = useAuth()
  const { navigate } = useTransition()
  const { openPalette } = useCommands()
  const isVisible = (n) => (!n.business || org?.type !== 'PERSONAL') && (!n.platform || isPlatformAdmin) && (!n.flag || flag(n.flag)) && (!n.perm || can(n.perm))
  const groups = NAV_GROUPS.map((group) => group.filter(isVisible)).filter((group) => group.length > 0)

  async function onLogout() {
    await logout()
    toast('success', t('logout'))
    navigate('/')
  }

  return (
    <aside className="sun-sidebar">
      <TransitionLink to="/" className="sun-sidebar__brand">
        <Icon name="sun" size={22} color="var(--green-600)" strokeWidth={2.2} />
        <span>{t('brand')}</span>
      </TransitionLink>
      <nav className="sun-sidebar__nav">
        {groups.map((group, gi) => (
          <div className="sun-nav-group" key={gi}>
            {gi > 0 && <div className="sun-nav-sep" aria-hidden="true" />}
            {group.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) => `sun-nav-item${isActive ? ' sun-nav-item--active' : ''}`}
              >
                <Icon name={n.icon} size={18} />
                <span>{t(`items.${n.key}`)}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sun-sidebar__foot">
        <NotificationBell />
        <button type="button" className="sun-nav-item" onClick={openPalette}>
          <Icon name="command" size={18} /><span>{t('commands')}</span>
          <span className="kbd" style={{ marginLeft: 'auto' }}>{formatShortcut({ mod: true, code: 'KeyK' }, isMac())}</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
          <LanguageSwitcher />
          <ThemeToggle style={{ marginLeft: 'auto' }} />
        </div>
        <WorkspaceSwitcher />
        <div className="sun-userchip">
          <span className="sun-avatar">{initials(user?.full_name)}</span>
          <div className="sun-userchip__meta">
            <strong>{user?.full_name || t('user')}</strong>
            <span>{org?.nombre || t('myWorkspace')}</span>
          </div>
          <IconBtn icon="log-out" label={t('logout')} size="sm" onClick={onLogout} style={{ marginLeft: 'auto' }} />
        </div>
      </div>
    </aside>
  )
}

function useRouteFocus(mainRef) {
  const { t } = useTranslation('nav')
  const location = useLocation()
  const [announcement, setAnnouncement] = useState('')
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    const match = [...NAV].reverse().find((n) => (n.end ? location.pathname === n.to : location.pathname.startsWith(n.to)))
    const label = match ? t(`items.${match.key}`) : t('brand')
    setAnnouncement(t('pageLoaded', { label }))
    if (mainRef.current) mainRef.current.focus({ preventScroll: true })
  }, [location.pathname, mainRef, t])
  return announcement
}

export function AppLayout() {
  const { t } = useTranslation('nav')
  const mainRef = useRef(null)
  const announcement = useRouteFocus(mainRef)
  return (
    <div className="sun-app">
      <a className="sun-skip-link" href="#main">{t('skipToContent')}</a>
      <Sidebar />
      <main id="main" ref={mainRef} tabIndex={-1} className="sun-main">
        <Outlet />
      </main>
      <HelpAssist />
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">{announcement}</div>
    </div>
  )
}

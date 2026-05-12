import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Icon, IconBtn } from '@/shared/ui'
import { TransitionLink, useTransition } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { toast } from '@/services/toast'

const NAV = [
  { to: '/app', label: 'Resumen', icon: 'layout-dashboard', end: true },
  { to: '/app/proyectos', label: 'Proyectos', icon: 'folder' },
  { to: '/app/diseno', label: 'Diseño', icon: 'sliders-horizontal' },
  { to: '/app/equipos', label: 'Equipos', icon: 'package' },
  { to: '/app/equipo', label: 'Equipo', icon: 'users', business: true },
  { to: '/app/memoria', label: 'Memoria', icon: 'file-text' },
]

function initials(name) {
  if (!name) return 'U'
  return name.trim().split(/\s+/).slice(0, 2).map((s) => s[0]?.toUpperCase()).join('') || 'U'
}

function Sidebar() {
  const { user, org, logout } = useAuth()
  const { navigate } = useTransition()
  const items = NAV.filter((n) => !n.business || org?.type !== 'PERSONAL')

  async function onLogout() {
    await logout()
    toast('success', 'Sesión cerrada')
    navigate('/')
  }

  return (
    <aside className="sun-sidebar">
      <TransitionLink to="/" className="sun-sidebar__brand">
        <Icon name="sun" size={22} color="var(--green-600)" strokeWidth={2.2} />
        <span>Sunalyze</span>
      </TransitionLink>
      <nav className="sun-sidebar__nav">
        {items.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) => `sun-nav-item${isActive ? ' sun-nav-item--active' : ''}`}
          >
            <Icon name={n.icon} size={18} />
            <span>{n.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sun-sidebar__foot">
        <button className="sun-nav-item"><Icon name="settings" size={18} /><span>Ajustes</span></button>
        <div className="sun-userchip">
          <span className="sun-avatar">{initials(user?.full_name)}</span>
          <div className="sun-userchip__meta">
            <strong>{user?.full_name || 'Usuario'}</strong>
            <span>{org?.nombre || 'Mi espacio'}</span>
          </div>
          <IconBtn icon="log-out" label="Cerrar sesión" size="sm" onClick={onLogout} style={{ marginLeft: 'auto' }} />
        </div>
      </div>
    </aside>
  )
}

function routeLabel(pathname) {
  const match = [...NAV].reverse().find((n) => (n.end ? pathname === n.to : pathname.startsWith(n.to)))
  return match?.label || 'Sunalyze'
}

function useRouteFocus(mainRef) {
  const location = useLocation()
  const [announcement, setAnnouncement] = useState('')
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    const label = routeLabel(location.pathname)
    setAnnouncement(`${label}, página cargada`)
    if (mainRef.current) mainRef.current.focus({ preventScroll: true })
  }, [location.pathname, mainRef])
  return announcement
}

export function AppLayout() {
  const mainRef = useRef(null)
  const announcement = useRouteFocus(mainRef)
  return (
    <div className="sun-app">
      <a className="sun-skip-link" href="#main">Saltar al contenido</a>
      <Sidebar />
      <main id="main" ref={mainRef} tabIndex={-1} className="sun-main">
        <Outlet />
      </main>
      <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">{announcement}</div>
    </div>
  )
}

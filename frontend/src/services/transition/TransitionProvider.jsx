import { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { TransitionContext } from './context'
import './transition.css'

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function TransitionProvider({ children, duration = 560, color = '#111' }) {
  const routerNavigate = useNavigate()
  const [phase, setPhase] = useState('idle')
  const pending = useRef(null)
  const busy = useRef(false)

  const navigate = useCallback((to, options) => {
    if (to == null || busy.current) return
    if (prefersReducedMotion()) {
      routerNavigate(to, options)
      window.scrollTo(0, 0)
      return
    }
    busy.current = true
    pending.current = { to, options }
    setPhase('cover')
  }, [routerNavigate])

  useEffect(() => {
    if (phase === 'cover') {
      const t = setTimeout(() => {
        const next = pending.current
        pending.current = null
        if (next) {
          routerNavigate(next.to, next.options)
          window.scrollTo(0, 0)
        }
        setPhase('reveal')
      }, duration + 30)
      return () => clearTimeout(t)
    }
    if (phase === 'reveal') {
      const t = setTimeout(() => {
        setPhase('idle')
        busy.current = false
      }, duration + 30)
      return () => clearTimeout(t)
    }
  }, [phase, duration, routerNavigate])

  const value = useMemo(() => ({ navigate, phase, busy: busy.current }), [navigate, phase])

  return (
    <TransitionContext.Provider value={value}>
      {children}
      <div
        className={`sun-trans sun-trans--${phase}`}
        style={{ '--trans-dur': duration + 'ms', '--trans-color': color }}
        aria-hidden="true"
      >
        <div className="sun-trans__mark">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </svg>
        </div>
      </div>
    </TransitionContext.Provider>
  )
}

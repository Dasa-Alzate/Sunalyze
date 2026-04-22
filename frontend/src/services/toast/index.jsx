import { useState, useEffect } from 'react'
import { Icon } from '@/shared/ui'

let listeners = []
let seq = 0

export function toast(tone, title, message) {
  const item = { id: ++seq, tone, title, message }
  listeners.forEach((fn) => fn(item))
  return item.id
}

export function subscribe(fn) {
  listeners.push(fn)
  return () => {
    listeners = listeners.filter((l) => l !== fn)
  }
}

const TOAST_ICONS = { success: 'check-circle-2', error: 'x-circle', info: 'info', warning: 'alert-triangle' }

export function ToastHost() {
  const [items, setItems] = useState([])
  useEffect(() => subscribe((item) => {
    setItems((prev) => [...prev, item])
    setTimeout(() => setItems((prev) => prev.filter((i) => i.id !== item.id)), 2800)
  }), [])
  return (
    <div style={{ position: 'fixed', right: 24, bottom: 24, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 10 }}>
      {items.map((it) => (
        <div key={it.id} className={`sun-toast sun-toast--${it.tone}`} style={{ animation: 'sunToastIn .2s ease-out' }}>
          <span className="sun-toast__icon"><Icon name={TOAST_ICONS[it.tone] || 'info'} size={18} /></span>
          <div className="sun-toast__body">
            <div className="sun-toast__title">{it.title}</div>
            {it.message && <div className="sun-toast__msg">{it.message}</div>}
          </div>
        </div>
      ))}
    </div>
  )
}

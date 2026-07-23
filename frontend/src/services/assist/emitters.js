import { setApiErrorHandler } from '@/api/client'

function describeTarget(el) {
  const tagged = el.closest('[data-assist]')
  if (tagged) return tagged.getAttribute('data-assist')
  const actionable = el.closest('button, a, [role="button"], [role="option"], [role="tab"]')
  if (!actionable) return null
  const label = actionable.getAttribute('aria-label')
    || actionable.textContent?.trim().slice(0, 40)
    || actionable.className?.toString().split(/\s+/)[0]
    || actionable.tagName.toLowerCase()
  return `${actionable.tagName.toLowerCase()}:${label}`
}

export function attachClickEmitter(bus) {
  function onClick(e) {
    if (!(e.target instanceof Element)) return
    const target = describeTarget(e.target)
    if (target) bus.emit('dom.click', { target })
  }
  document.addEventListener('click', onClick, true)
  return () => document.removeEventListener('click', onClick, true)
}

export function attachJsErrorEmitter(bus) {
  function onError(e) {
    bus.emit('js.error', { message: String(e.message || e.reason?.message || e.reason || 'error').slice(0, 200) })
  }
  window.addEventListener('error', onError)
  window.addEventListener('unhandledrejection', onError)
  return () => {
    window.removeEventListener('error', onError)
    window.removeEventListener('unhandledrejection', onError)
  }
}

export function attachApiErrorEmitter(bus) {
  if (typeof setApiErrorHandler !== 'function') return () => {}
  setApiErrorHandler((path, status, message, code) => {
    bus.emit('api.error', { path, status, code: code || null, message: String(message || '').slice(0, 200) })
  })
  return () => setApiErrorHandler(null)
}

const RAGE_THRESHOLD = 4
const RAGE_WINDOW_MS = 5000
const RAGE_COOLDOWN_MS = 30000

export function attachRageDetector(bus) {
  const hits = new Map()
  const muted = new Map()
  return bus.on('dom.click', (event) => {
    const target = event.data.target
    const now = event.t
    const mutedUntil = muted.get(target) || 0
    if (now < mutedUntil) return
    const times = (hits.get(target) || []).filter((t) => now - t < RAGE_WINDOW_MS)
    times.push(now)
    hits.set(target, times)
    if (times.length >= RAGE_THRESHOLD) {
      hits.delete(target)
      muted.set(target, now + RAGE_COOLDOWN_MS)
      bus.emit('assist.frustration', { target, count: times.length })
    }
  })
}

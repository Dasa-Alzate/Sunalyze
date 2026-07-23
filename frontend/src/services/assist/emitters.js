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
  setApiErrorHandler((path, status, message) => {
    bus.emit('api.error', { path, status, message: String(message || '').slice(0, 200) })
  })
  return () => setApiErrorHandler(null)
}

export function createBus() {
  const listeners = new Map()

  function on(type, fn) {
    if (!listeners.has(type)) listeners.set(type, new Set())
    listeners.get(type).add(fn)
    return () => listeners.get(type)?.delete(fn)
  }

  function emit(type, data = {}) {
    const event = { type, t: Date.now(), data }
    listeners.get(type)?.forEach((fn) => { try { fn(event) } catch { void 0 } })
    listeners.get('*')?.forEach((fn) => { try { fn(event) } catch { void 0 } })
    return event
  }

  return { on, emit }
}

import { useState, useRef, useCallback } from 'react'

export function useAsyncAction(fn) {
  const [busy, setBusy] = useState(false)
  const inFlight = useRef(false)

  const run = useCallback((...args) => {
    if (inFlight.current) return undefined
    const result = fn ? fn(...args) : undefined
    if (result && typeof result.then === 'function') {
      inFlight.current = true
      setBusy(true)
      Promise.resolve(result).finally(() => {
        inFlight.current = false
        setBusy(false)
      })
    }
    return result
  }, [fn])

  return [run, busy]
}

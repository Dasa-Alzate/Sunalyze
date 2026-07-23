import { useEffect, useRef } from 'react'

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function focusable(container) {
  return Array.from(container.querySelectorAll(FOCUSABLE)).filter(
    (el) => el.offsetParent !== null || el === document.activeElement,
  )
}

export function useFocusTrap(active = true) {
  const ref = useRef(null)

  useEffect(() => {
    if (!active) return undefined
    const container = ref.current
    if (!container) return undefined

    const trigger = document.activeElement
    const hidden = []
    let node = container
    while (node && node !== document.body) {
      const parent = node.parentElement
      if (parent) {
        for (const sibling of parent.children) {
          if (sibling === node || sibling.hasAttribute('aria-hidden')) continue
          if (sibling.classList.contains('sun-scrim__backdrop')) continue
          if (sibling.matches('[aria-live],[role="status"],[role="alert"]')) continue
          if (sibling.querySelector('[aria-live],[role="status"],[role="alert"]')) continue
          sibling.setAttribute('aria-hidden', 'true')
          sibling.setAttribute('inert', '')
          hidden.push(sibling)
        }
      }
      node = parent
    }

    const items = focusable(container)
    const initial = items[0] || container
    if (initial === container && !container.hasAttribute('tabindex')) {
      container.setAttribute('tabindex', '-1')
    }
    initial.focus({ preventScroll: true })

    function onKey(e) {
      if (e.key !== 'Tab') return
      const current = focusable(container)
      if (current.length === 0) {
        e.preventDefault()
        return
      }
      const first = current[0]
      const last = current[current.length - 1]
      const activeEl = document.activeElement
      if (e.shiftKey) {
        if (activeEl === first || !container.contains(activeEl)) {
          e.preventDefault()
          last.focus()
        }
      } else if (activeEl === last || !container.contains(activeEl)) {
        e.preventDefault()
        first.focus()
      }
    }

    container.addEventListener('keydown', onKey)

    return () => {
      container.removeEventListener('keydown', onKey)
      hidden.forEach((el) => {
        el.removeAttribute('aria-hidden')
        el.removeAttribute('inert')
      })
      if (trigger && typeof trigger.focus === 'function') {
        trigger.focus({ preventScroll: true })
      }
    }
  }, [active])

  return ref
}

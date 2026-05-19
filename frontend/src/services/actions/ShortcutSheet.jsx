import { useEffect } from 'react'
import { Icon, IconBtn } from '@/shared/ui'
import { useFocusTrap } from '@/shared/useFocusTrap'
import { getActions, formatShortcut } from './registry'

function grouped(actions) {
  const map = new Map()
  for (const a of actions) {
    if (!a.shortcut) continue
    if (!map.has(a.group)) map.set(a.group, [])
    map.get(a.group).push(a)
  }
  return Array.from(map.entries())
}

export function ShortcutSheet({ onClose, mac }) {
  const trapRef = useFocusTrap(true)
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const groups = grouped(getActions())

  return (
    <div className="sun-scrim sun-scrim--center" role="presentation">
      <button type="button" className="sun-scrim__backdrop" aria-label="Cerrar" onClick={onClose} />
      <div
        ref={trapRef}
        className="sun-shortsheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sun-shortsheet-title"
      >
        <header className="sun-shortsheet__head">
          <h2 id="sun-shortsheet-title">
            <Icon name="keyboard" size={18} /> Atajos de teclado
          </h2>
          <IconBtn icon="x" label="Cerrar" size="sm" onClick={onClose} />
        </header>
        <div className="sun-shortsheet__body">
          {groups.map(([group, actions]) => (
            <section key={group} className="sun-shortsheet__group">
              <h3 className="sun-shortsheet__grouptitle">{group}</h3>
              <ul>
                {actions.map((a) => (
                  <li key={a.id} className="sun-shortsheet__row">
                    <span>{a.label}</span>
                    <span className="kbd">{formatShortcut(a.shortcut, mac)}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}

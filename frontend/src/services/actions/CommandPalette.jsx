import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Icon } from '@/shared/ui'
import { useFocusTrap } from '@/shared/useFocusTrap'
import { getActions, formatShortcut } from './registry'
import { filterActions } from './fuzzy'

export function CommandPalette({ onClose, onRun, mac }) {
  const trapRef = useFocusTrap(true)
  const inputRef = useRef(null)
  const listRef = useRef(null)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const rawId = useId()
  const baseId = `cmdk${rawId.replace(/[^a-zA-Z0-9]/g, '')}`
  const listId = `${baseId}-list`

  const results = useMemo(() => filterActions(query, getActions()), [query])

  useEffect(() => {
    setActive(0)
  }, [query])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const el = document.getElementById(`${baseId}-opt-${active}`)
    if (el && typeof el.scrollIntoView === 'function') el.scrollIntoView({ block: 'nearest' })
  }, [active, baseId])

  function choose(action) {
    if (!action) return
    onClose()
    onRun(action)
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((i) => (results.length ? (i + 1) % results.length : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((i) => (results.length ? (i - 1 + results.length) % results.length : 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      choose(results[active])
    }
  }

  const activeId = results.length ? `${baseId}-opt-${active}` : undefined

  return (
    <div className="sun-scrim sun-scrim--center" role="presentation">
      <button type="button" className="sun-scrim__backdrop" aria-label="Cerrar" onClick={onClose} />
      <div
        ref={trapRef}
        className="sun-cmdk"
        role="dialog"
        aria-modal="true"
        aria-label="Paleta de comandos"
      >
        <div className="sun-cmdk__search">
          <Icon name="search" size={18} />
          <input
            ref={inputRef}
            className="sun-cmdk__input"
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={activeId}
            aria-autocomplete="list"
            aria-label="Buscar comando"
            placeholder="Buscar comando o acción…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
          />
        </div>
        <ul ref={listRef} id={listId} role="listbox" aria-label="Comandos" className="sun-cmdk__list">
          {results.length === 0 && (
            <li className="sun-cmdk__empty" role="option" aria-selected="false" aria-disabled="true">
              Sin resultados
            </li>
          )}
          {results.map((action, i) => (
            <li
              key={action.id}
              id={`${baseId}-opt-${i}`}
              role="option"
              aria-selected={i === active}
              className={`sun-cmdk__opt${i === active ? ' sun-cmdk__opt--active' : ''}`}
              onMouseMove={() => setActive(i)}
              onClick={() => choose(action)}
            >
              <span className="sun-cmdk__opt-label">{action.label}</span>
              <span className="sun-cmdk__opt-group">{action.group}</span>
              {action.shortcut && <span className="kbd">{formatShortcut(action.shortcut, mac)}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

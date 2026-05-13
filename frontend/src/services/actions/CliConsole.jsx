import { useCallback, useEffect, useRef, useState } from 'react'
import { Icon, IconBtn } from '@/shared/ui'
import { useFocusTrap } from '@/shared/useFocusTrap'
import { runCommand, autocomplete, commonPrefix } from './commands'

const HISTORY_KEY = 'sunalyze.cli.history'
const HISTORY_CAP = 50

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === 'string') : []
  } catch {
    return []
  }
}

function saveHistory(list) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(-HISTORY_CAP)))
  } catch {
    return
  }
}

export function CliConsole({ onClose, ctx }) {
  const trapRef = useFocusTrap(true)
  const inputRef = useRef(null)
  const logRef = useRef(null)
  const [value, setValue] = useState('')
  const [entries, setEntries] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const history = useRef(loadHistory())
  const cursor = useRef(history.current.length)
  const draft = useRef('')

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    setSuggestions(autocomplete(value))
  }, [value])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [entries])

  const append = useCallback((entry) => {
    setEntries((prev) => [...prev, entry])
  }, [])

  const submit = useCallback(() => {
    const command = value.trim()
    if (!command) return
    append({ kind: 'input', text: command })
    const result = runCommand(command, ctx)
    append({ kind: result.ok ? 'output' : 'error', text: result.message })
    const next = history.current.filter((h, i) => !(i === history.current.length - 1 && h === command))
    next.push(command)
    history.current = next.slice(-HISTORY_CAP)
    saveHistory(history.current)
    cursor.current = history.current.length
    draft.current = ''
    setValue('')
  }, [value, ctx, append])

  const applyCompletion = useCallback(() => {
    const options = autocomplete(value)
    if (options.length === 0) return
    const tokens = value.split(/\s+/)
    const endsWithSpace = /\s$/.test(value)
    const before = endsWithSpace ? value : tokens.slice(0, -1).join(' ')
    const completion = options.length === 1 ? options[0] : commonPrefix(options)
    if (!completion) return
    const prefix = before ? `${before} ` : ''
    const filled = `${prefix}${completion}`
    setValue(options.length === 1 ? `${filled} ` : filled)
  }, [value])

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'Enter') {
      e.preventDefault()
      submit()
    } else if (e.key === 'Tab') {
      e.preventDefault()
      applyCompletion()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (history.current.length === 0) return
      if (cursor.current === history.current.length) draft.current = value
      cursor.current = Math.max(0, cursor.current - 1)
      setValue(history.current[cursor.current])
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (cursor.current >= history.current.length) return
      cursor.current += 1
      setValue(cursor.current === history.current.length ? draft.current : history.current[cursor.current])
    }
  }

  return (
    <div className="sun-scrim sun-scrim--center" role="presentation">
      <button type="button" className="sun-scrim__backdrop" aria-label="Cerrar" onClick={onClose} />
      <div
        ref={trapRef}
        className="sun-cli"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sun-cli-title"
      >
        <header className="sun-cli__head">
          <h2 id="sun-cli-title">
            <Icon name="terminal" size={18} /> Consola
          </h2>
          <IconBtn icon="x" label="Cerrar" size="sm" onClick={onClose} />
        </header>
        <div ref={logRef} className="sun-cli__log" role="log" aria-live="polite" aria-label="Salida de la consola">
          {entries.length === 0 && (
            <p className="sun-cli__hint">Escribe un comando. Prueba <code>help</code>.</p>
          )}
          {entries.map((entry, i) => (
            <p key={i} className={`sun-cli__line sun-cli__line--${entry.kind}`}>
              {entry.kind === 'input' && <span className="sun-cli__prompt" aria-hidden="true">›</span>}
              <span className="sun-cli__text">{entry.text}</span>
            </p>
          ))}
        </div>
        <div className="sun-cli__prompt-row">
          <span className="sun-cli__caret" aria-hidden="true">›</span>
          <input
            ref={inputRef}
            className="sun-cli__input"
            type="text"
            aria-label="Comando"
            autoComplete="off"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck="false"
            placeholder="goto projects"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
          />
        </div>
        {suggestions.length > 0 && (
          <ul className="sun-cli__suggest" aria-label="Sugerencias">
            {suggestions.map((s) => (
              <li key={s} className="sun-cli__suggest-item">{s}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

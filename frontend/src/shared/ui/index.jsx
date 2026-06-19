import { useState, useRef, useEffect, useId } from 'react'
import * as Lucide from 'lucide-react'
import { useAsyncAction } from '@/shared/useAsyncAction'

function pascal(name) {
  return name.split('-').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join('')
}

export function Icon({ name, size = 18, color, strokeWidth = 2, style, ...rest }) {
  const Cmp = Lucide[pascal(name)] || Lucide.Square
  return (
    <Cmp
      size={size}
      color={color}
      strokeWidth={strokeWidth}
      style={{ display: 'inline-block', verticalAlign: 'middle', flex: 'none', ...style }}
      {...rest}
    />
  )
}

export function Btn({ variant = 'primary', size = 'md', icon, iconRight, block, children, onClick, disabled, busy, ...rest }) {
  const [guardedClick, autoBusy] = useAsyncAction(onClick)
  const isBusy = busy || autoBusy
  const cls = [
    'sun-btn',
    `sun-btn--${variant}`,
    size !== 'md' ? `sun-btn--${size}` : '',
    block ? 'sun-btn--block' : '',
  ].filter(Boolean).join(' ')
  return (
    <button
      className={cls}
      onClick={onClick ? guardedClick : undefined}
      disabled={disabled || isBusy}
      data-busy={isBusy ? 'true' : undefined}
      {...rest}
    >
      {icon && <Icon name={icon} size={16} />}
      {children && <span>{children}</span>}
      {iconRight && <Icon name={iconRight} size={16} />}
    </button>
  )
}

export function IconBtn({ icon, label, bordered, size = 'md', onClick, disabled, ...rest }) {
  const [guardedClick, busy] = useAsyncAction(onClick)
  const cls = [
    'sun-iconbtn',
    bordered ? 'sun-iconbtn--bordered' : '',
    size === 'sm' ? 'sun-iconbtn--sm' : '',
  ].filter(Boolean).join(' ')
  return (
    <button
      className={cls}
      aria-label={label}
      title={label}
      onClick={onClick ? guardedClick : undefined}
      disabled={disabled || busy}
      data-busy={busy ? 'true' : undefined}
      {...rest}
    >
      <Icon name={icon} size={size === 'sm' ? 16 : 18} />
    </button>
  )
}

export function Badge({ tone = 'neutral', icon, children }) {
  return (
    <span className={`sun-badge sun-badge--${tone}`}>
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  )
}

export function Dot({ state = 'pending' }) {
  return <span className={`sun-statusdot sun-statusdot--${state}`} />
}

export function Metric({ label, value, unit, stale, info }) {
  return (
    <div className={`sun-metric${stale ? ' sun-metric--stale' : ''}`}>
      <span className="sun-metric__label">
        {label}
        {info && <Icon name="info" size={12} />}
        {stale && <Icon name="alert-triangle" size={12} color="var(--state-warn)" />}
      </span>
      <span className="sun-metric__value">
        {value}
        {unit && <span className="unit">{unit}</span>}
      </span>
    </div>
  )
}

export function Field({ id, label, hint, error, required, icon, numeric, children, ...rest }) {
  const autoId = useId()
  const fieldId = id || autoId
  const msgId = `${fieldId}-msg`
  const describedBy = error || hint ? msgId : undefined
  const control = children || (
    <input
      id={fieldId}
      className="sun-input"
      data-numeric={numeric ? '' : undefined}
      aria-invalid={error ? 'true' : undefined}
      aria-describedby={describedBy}
      aria-required={required ? 'true' : undefined}
      {...rest}
    />
  )
  return (
    <div className="sun-field">
      {label && (
        <label className="sun-field__label" htmlFor={fieldId}>
          {label}
          {required && <span className="req">*</span>}
        </label>
      )}
      {icon ? (
        <div className="sun-input-group">
          <span className="sun-input-group__icon"><Icon name={icon} size={16} /></span>
          {control}
        </div>
      ) : control}
      {error ? (
        <span id={msgId} className="sun-field__error"><Icon name="alert-circle" size={13} />{error}</span>
      ) : hint ? (
        <span id={msgId} className="sun-field__hint">{hint}</span>
      ) : null}
    </div>
  )
}

export function SelectField({ id, label, options = [], children, ...rest }) {
  const autoId = useId()
  const fieldId = id || autoId
  return (
    <div className="sun-field">
      {label && <label className="sun-field__label" htmlFor={fieldId}>{label}</label>}
      <select id={fieldId} className="sun-select" {...rest}>
        {children}
        {options.map((o) => {
          const v = typeof o === 'object' ? o.value : o
          const t = typeof o === 'object' ? o.label : o
          return <option key={v} value={v}>{t}</option>
        })}
      </select>
    </div>
  )
}

export function Card({ className = '', children, ...rest }) {
  return <div className={`sun-card ${className}`} {...rest}>{children}</div>
}

export function Scrim({ onClose, label = 'Diálogo', children }) {
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose && onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="sun-scrim" role="dialog" aria-modal="true" aria-label={label}>
      <button type="button" className="sun-scrim__backdrop" aria-label="Cerrar" onClick={onClose} />
      {children}
    </div>
  )
}

const FORMATS = {
  copy: { icon: 'clipboard', label: 'Copiar al portapapeles', kbd: '⌘C' },
  csv: { icon: 'table', label: 'CSV (.csv)' },
  xlsx: { icon: 'file-spreadsheet', label: 'Excel (.xlsx)' },
  pdf: { icon: 'file-text', label: 'PDF (.pdf)' },
}

export function ExportMenu({
  label = 'Exportar',
  formats = ['copy', 'csv', 'xlsx', 'pdf'],
  onExport,
  align = 'right',
  variant = 'secondary',
  size = 'sm',
  iconOnly = false,
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])
  function pick(f) {
    setOpen(false)
    onExport && onExport(f)
  }
  return (
    <div className="sun-menu-wrap" ref={ref}>
      {iconOnly ? (
        <IconBtn icon="download" label={label} bordered size={size} aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)} />
      ) : (
        <Btn variant={variant} size={size} icon="download" iconRight="chevron-down" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>{label}</Btn>
      )}
      {open && (
        <div className={`sun-menu sun-menu--${align}`} role="menu">
          <div className="sun-menu__label">Exportar como</div>
          {formats.map((f) => {
            const m = FORMATS[f]
            return m ? (
              <button key={f} className="sun-menu__item" role="menuitem" onClick={() => pick(f)}>
                <Icon name={m.icon} size={16} /><span>{m.label}</span>{m.kbd && <span className="kbd">{m.kbd}</span>}
              </button>
            ) : null
          })}
        </div>
      )}
    </div>
  )
}

export function Spinner({ label = 'Cargando…' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
      <Icon name="loader-2" size={20} style={{ animation: 'sunSpin 0.8s linear infinite' }} />
      <span>{label}</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="sun-empty">
      <div className="sun-empty__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}>
        <Icon name="alert-triangle" size={26} />
      </div>
      <div className="sun-empty__title">Algo ha fallado</div>
      <div className="sun-empty__desc">{message || 'No se pudieron cargar los datos.'}</div>
      {onRetry && (
        <div className="sun-empty__actions">
          <Btn variant="secondary" icon="refresh-cw" onClick={onRetry}>Reintentar</Btn>
        </div>
      )}
    </div>
  )
}

export function Topbar({ title, crumb, actions }) {
  return (
    <header className="sun-topbar">
      <div className="sun-topbar__title">
        {crumb && <span className="sun-topbar__crumb">{crumb}<Icon name="chevron-right" size={14} /></span>}
        <h1>{title}</h1>
      </div>
      <div className="sun-topbar__actions">{actions}</div>
    </header>
  )
}

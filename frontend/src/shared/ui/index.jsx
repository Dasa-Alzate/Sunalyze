import { useState, useRef, useEffect, useId } from 'react'
import * as Lucide from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAsyncAction } from '@/shared/useAsyncAction'
import { useFocusTrap } from '@/shared/useFocusTrap'

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
      aria-busy={isBusy ? 'true' : undefined}
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
      aria-busy={busy ? 'true' : undefined}
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

export function Scrim({ onClose, label, children }) {
  const { t } = useTranslation('common')
  const trapRef = useFocusTrap(true)
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose && onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div ref={trapRef} className="sun-scrim" role="dialog" aria-modal="true" aria-label={label || t('dialog')}>
      <button type="button" className="sun-scrim__backdrop" aria-label={t('actions.close')} onClick={onClose} />
      {children}
    </div>
  )
}

const FORMATS = {
  copy: { icon: 'clipboard', tkey: 'export.copy', kbd: '⌘C' },
  csv: { icon: 'table', tkey: 'export.csv' },
  xlsx: { icon: 'file-spreadsheet', tkey: 'export.xlsx' },
  pdf: { icon: 'file-text', tkey: 'export.pdf' },
}

export function ExportMenu({
  label,
  formats = ['copy', 'csv', 'xlsx', 'pdf'],
  onExport,
  align = 'right',
  variant = 'secondary',
  size = 'sm',
  iconOnly = false,
}) {
  const { t } = useTranslation('common')
  const menuLabel = label || t('actions.export')
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const triggerRef = useRef(null)
  const itemsRef = useRef([])
  const menuId = useId()
  const valid = formats.filter((f) => FORMATS[f])

  useEffect(() => {
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  useEffect(() => {
    if (open) itemsRef.current[0]?.focus()
  }, [open])

  function close(returnFocus = true) {
    setOpen(false)
    if (returnFocus) triggerRef.current?.focus()
  }

  function pick(f) {
    close()
    onExport && onExport(f)
  }

  function onMenuKey(e) {
    const items = itemsRef.current.filter(Boolean)
    const idx = items.indexOf(document.activeElement)
    if (e.key === 'Escape') {
      e.preventDefault()
      close()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      items[(idx + 1) % items.length]?.focus()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      items[(idx - 1 + items.length) % items.length]?.focus()
    } else if (e.key === 'Home') {
      e.preventDefault()
      items[0]?.focus()
    } else if (e.key === 'End') {
      e.preventDefault()
      items[items.length - 1]?.focus()
    } else if (e.key === 'Tab') {
      close(false)
    }
  }

  function onTriggerKey(e) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      setOpen(true)
    }
  }

  const triggerProps = {
    ref: triggerRef,
    'aria-haspopup': 'menu',
    'aria-expanded': open,
    'aria-controls': open ? menuId : undefined,
    onClick: () => setOpen((o) => !o),
    onKeyDown: onTriggerKey,
  }

  return (
    <div className="sun-menu-wrap" ref={ref}>
      {iconOnly ? (
        <IconBtn icon="download" label={menuLabel} bordered size={size} {...triggerProps} />
      ) : (
        <Btn variant={variant} size={size} icon="download" iconRight="chevron-down" {...triggerProps}>{menuLabel}</Btn>
      )}
      {open && (
        <div id={menuId} className={`sun-menu sun-menu--${align}`} role="menu" aria-label={menuLabel} tabIndex={-1} onKeyDown={onMenuKey}>
          <div className="sun-menu__label">{t('export.as')}</div>
          {valid.map((f, i) => {
            const m = FORMATS[f]
            return (
              <button
                key={f}
                ref={(el) => { itemsRef.current[i] = el }}
                className="sun-menu__item"
                role="menuitem"
                tabIndex={-1}
                onClick={() => pick(f)}
              >
                <Icon name={m.icon} size={16} /><span>{t(m.tkey)}</span>{m.kbd && <span className="kbd">{m.kbd}</span>}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function Spinner({ label }) {
  const { t } = useTranslation('common')
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
      <Icon name="loader-2" size={20} style={{ animation: 'sunSpin 0.8s linear infinite' }} />
      <span>{label || t('state.loading')}</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  const { t } = useTranslation('common')
  return (
    <div className="sun-empty">
      <div className="sun-empty__icon" style={{ background: 'var(--danger-soft)', color: 'var(--danger)' }}>
        <Icon name="alert-triangle" size={26} />
      </div>
      <div className="sun-empty__title">{t('state.errorTitle')}</div>
      <div className="sun-empty__desc">{message || t('state.errorDesc')}</div>
      {onRetry && (
        <div className="sun-empty__actions">
          <Btn variant="secondary" icon="refresh-cw" onClick={onRetry}>{t('actions.retry')}</Btn>
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

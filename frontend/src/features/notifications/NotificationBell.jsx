import { useTranslation } from 'react-i18next'
import { Icon } from '@/shared/ui'
import { useNotifications } from '@/services/notifications'
import NotificationCenter from './NotificationCenter'

export default function NotificationBell() {
  const { t } = useTranslation('notifications')
  const { count, open, setOpen } = useNotifications()

  const label = count > 0 ? t('bell.labelWithCount', { count }) : t('bell.label')

  return (
    <>
      <button
        type="button"
        className="sun-nav-item sun-notif-bell"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen(true)}
      >
        <span className="sun-notif-bell__icon">
          <Icon name="bell" size={18} />
          {count > 0 && (
            <span className="sun-notif-badge" aria-hidden="true">{count > 99 ? '99+' : count}</span>
          )}
        </span>
        <span>{t('bell.label')}</span>
      </button>
      <span className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {t('center.liveUnread', { count })}
      </span>
      {open && <NotificationCenter onClose={() => setOpen(false)} />}
    </>
  )
}

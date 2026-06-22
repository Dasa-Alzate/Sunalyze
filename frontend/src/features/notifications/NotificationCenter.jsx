import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Scrim, Btn, IconBtn, Icon, Spinner, ErrorState } from '@/shared/ui'
import { useTransition } from '@/services/transition'
import { useNotifications } from '@/services/notifications'

function toAppPath(link) {
  if (!link) return null
  return link.startsWith('/app') ? link : `/app${link}`
}

function NotificationItem({ item, onActivate, onMarkRead }) {
  const { t } = useTranslation('notifications')
  const unread = !item.read_at
  const text = t([`types.${item.type}`, 'types.default'])
  return (
    <li className={`sun-notif-item${unread ? ' sun-notif-item--unread' : ''}`}>
      <button type="button" className="sun-notif-item__main" onClick={() => onActivate(item)}>
        {unread && <span className="sun-notif-item__dot" aria-hidden="true" />}
        <span className="sun-notif-item__text">
          {text}
          {unread && <span className="sr-only"> · {t('center.unread')}</span>}
        </span>
      </button>
      {unread && (
        <IconBtn
          icon="check"
          size="sm"
          label={t('center.markRead')}
          onClick={() => onMarkRead(item.id)}
        />
      )}
    </li>
  )
}

export default function NotificationCenter({ onClose }) {
  const { t } = useTranslation('notifications')
  const { navigate } = useTransition()
  const { items, count, loading, error, hasMore, loadFirst, loadMore, markRead, readAll } = useNotifications()

  useEffect(() => {
    loadFirst()
  }, [loadFirst])

  async function activate(item) {
    await markRead(item.id)
    const path = toAppPath(item.link)
    onClose()
    if (path) navigate(path)
  }

  return (
    <Scrim label={t('center.title')} onClose={onClose}>
      <div className="sun-drawer sun-notif-center">
        <header className="sun-drawer__head">
          <h3>{t('center.title')}</h3>
          <div className="sun-notif-center__actions">
            <Btn variant="ghost" size="sm" icon="check-check" disabled={count === 0} onClick={readAll}>
              {t('center.markAll')}
            </Btn>
            <IconBtn icon="x" size="sm" label={t('bell.label')} onClick={onClose} />
          </div>
        </header>
        <div className="sun-drawer__body">
          {error ? (
            <ErrorState message={error} onRetry={loadFirst} />
          ) : loading && items.length === 0 ? (
            <Spinner />
          ) : items.length === 0 ? (
            <div className="sun-notif-empty">
              <Icon name="bell-off" size={26} />
              <p>{t('center.empty')}</p>
            </div>
          ) : (
            <>
              <ul className="sun-notif-list">
                {items.map((item) => (
                  <NotificationItem
                    key={item.id}
                    item={item}
                    onActivate={activate}
                    onMarkRead={markRead}
                  />
                ))}
              </ul>
              {hasMore && (
                <div className="sun-notif-center__more">
                  <Btn variant="secondary" size="sm" busy={loading} onClick={loadMore}>
                    {t('center.loadMore')}
                  </Btn>
                </div>
              )}
            </>
          )}
        </div>
        <span className="sr-only" role="status" aria-live="polite" aria-atomic="true">
          {t('center.liveUnread', { count })}
        </span>
      </div>
    </Scrim>
  )
}

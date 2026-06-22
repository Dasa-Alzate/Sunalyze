import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Topbar, Card, Btn, Icon, Spinner, ErrorState } from '@/shared/ui'
import { TransitionLink } from '@/services/transition'
import { useAuth } from '@/services/auth'
import { api } from '@/api/client'
import { dateTime } from '@/shared/format'

const PAGE_SIZE = 25

function toAppPath(link) {
  if (!link) return null
  return link.startsWith('/app') ? link : `/app${link}`
}

function actionLabel(t, action) {
  return t([`actions.${action}`, '_raw'], { defaultValue: action })
}

function ActivityRow({ item }) {
  const { t } = useTranslation('activity')
  const actor = item.actor_email || t('unknownActor')
  const path = toAppPath(item.link)
  return (
    <li className="sun-activity-item">
      <span className="sun-activity-item__icon" aria-hidden="true">
        <Icon name="activity" size={16} />
      </span>
      <div className="sun-activity-item__body">
        <p className="sun-activity-item__text">
          <strong>{actor}</strong> <span>{actionLabel(t, item.action)}</span>
        </p>
        <p className="sun-activity-item__meta">
          <time dateTime={item.created_at}>{dateTime(item.created_at)}</time>
        </p>
      </div>
      {path && (
        <TransitionLink to={path} className="sun-activity-item__link" aria-label={t('openTarget')}>
          <Icon name="arrow-up-right" size={16} />
        </TransitionLink>
      )}
    </li>
  )
}

export default function ActivityFeed() {
  const { t } = useTranslation('activity')
  const { can } = useAuth()
  const allowed = can('audit:view')
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async (offset) => {
    setLoading(true)
    setError(null)
    try {
      const page = await api.audit.feed({ limit: PAGE_SIZE, offset })
      setItems((prev) => (offset === 0 ? page.items : [...prev, ...page.items]))
      setTotal(page.total)
      setHasMore(page.has_more)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (allowed) load(0)
  }, [allowed, load])

  if (!allowed) {
    return (
      <>
        <Topbar title={t('title')} />
        <ErrorState message={t('subtitle')} />
      </>
    )
  }

  return (
    <>
      <Topbar title={t('title')} />
      <Card className="sun-card--pad">
        <p className="sun-activity__subtitle">{t('subtitle')}</p>
        {error ? (
          <ErrorState message={error} onRetry={() => load(0)} />
        ) : loading && items.length === 0 ? (
          <Spinner />
        ) : items.length === 0 ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="activity" size={26} /></div>
            <div className="sun-empty__desc">{t('empty')}</div>
          </div>
        ) : (
          <>
            <ul className="sun-activity-list">
              {items.map((item) => (
                <ActivityRow key={item.id} item={item} />
              ))}
            </ul>
            <div className="sun-activity__footer">
              <span className="sun-activity__count">{t('showing', { count: items.length, total })}</span>
              {hasMore && (
                <Btn variant="secondary" size="sm" busy={loading} onClick={() => load(items.length)}>
                  {t('loadMore')}
                </Btn>
              )}
            </div>
          </>
        )}
        <span className="sr-only" role="status" aria-live="polite" aria-atomic="true">
          {t('live', { count: items.length })}
        </span>
      </Card>
    </>
  )
}

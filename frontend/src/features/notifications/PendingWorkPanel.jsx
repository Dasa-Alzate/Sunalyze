import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, Icon, Btn, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { useTransition } from '@/services/transition'

function toAppPath(link) {
  if (!link) return null
  return link.startsWith('/app') ? link : `/app${link}`
}

export default function PendingWorkPanel() {
  const { t } = useTranslation('notifications')
  const { navigate } = useTransition()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  function load() {
    setError(null)
    setData(null)
    api.pendingWork.get().then(setData).catch((e) => setError(e.message))
  }
  useEffect(load, [])

  const items = data?.items || []

  return (
    <Card className="sun-card--pad">
      <div className="sun-section-title"><h3>{t('pending.title')}</h3></div>
      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : !data ? (
        <Spinner />
      ) : items.length === 0 ? (
        <div className="sun-notif-empty">
          <Icon name="check-circle-2" size={26} />
          <p>{t('pending.empty')}</p>
        </div>
      ) : (
        <ul className="sun-pending-list">
          {items.map((item) => {
            const path = toAppPath(item.link)
            const label = t([`pending.items.${item.type}`, ''], item.label)
            return (
              <li key={item.type} className="sun-pending-item">
                <span className="sun-pending-item__count" aria-hidden="true">{item.count}</span>
                <span className="sun-pending-item__label">{label}</span>
                <Btn
                  variant="ghost"
                  size="sm"
                  iconRight="arrow-right"
                  onClick={() => path && navigate(path)}
                  aria-label={`${t('pending.go')}: ${label}`}
                >
                  {t('pending.go')}
                </Btn>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}

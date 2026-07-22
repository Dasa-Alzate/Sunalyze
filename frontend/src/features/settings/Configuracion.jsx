import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Topbar, Icon } from '@/shared/ui'
import { useAuth } from '@/services/auth'
import BrandingSettings from '@/features/settings/BrandingSettings'
import Flags from '@/features/admin/Flags'

export default function Configuracion() {
  const { t } = useTranslation('settings')
  const { can, isPlatformAdmin } = useAuth()

  const tabs = useMemo(() => {
    const list = []
    if (can('org:manage')) {
      list.push({ key: 'marca', icon: 'palette', render: () => <BrandingSettings /> })
    }
    if (isPlatformAdmin) {
      list.push({ key: 'flags', icon: 'flag', render: () => <Flags /> })
    }
    return list
  }, [can, isPlatformAdmin])

  const [active, setActive] = useState(() => tabs[0]?.key)
  const current = tabs.find((tab) => tab.key === active) || tabs[0]

  return (
    <>
      <Topbar title={t('config.title')} crumb={t('config.crumb')} />
      <div className="sun-content">
        <div className="sun-cfg">
          <nav className="sun-cfg__nav" aria-label={t('config.nav')}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                className={`sun-cfg__tab${current?.key === tab.key ? ' sun-cfg__tab--active' : ''}`}
                aria-current={current?.key === tab.key ? 'page' : undefined}
                onClick={() => setActive(tab.key)}
              >
                <Icon name={tab.icon} size={18} />
                <span>{t(`config.tabs.${tab.key}`)}</span>
              </button>
            ))}
          </nav>
          <div className="sun-cfg__body">
            {current ? current.render() : null}
          </div>
        </div>
      </div>
    </>
  )
}

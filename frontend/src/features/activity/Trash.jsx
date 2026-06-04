import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Topbar, Card, Btn, Icon, Scrim, Spinner, ErrorState } from '@/shared/ui'
import { useAuth } from '@/services/auth'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { dateTime } from '@/shared/format'

function ConfirmRestore({ kind, name, onCancel, onConfirm }) {
  const { t } = useTranslation('trash')
  return (
    <Scrim label={t('confirm.title')} onClose={onCancel}>
      <div className="sun-drawer sun-confirm">
        <header className="sun-drawer__head"><h3>{t('confirm.title')}</h3></header>
        <div className="sun-drawer__body">
          <p>{t(`confirm.${kind}`, { name })}</p>
        </div>
        <footer className="sun-drawer__foot">
          <Btn variant="secondary" onClick={onCancel}>{t('confirm.cancel')}</Btn>
          <Btn icon="rotate-ccw" onClick={onConfirm}>{t('confirm.accept')}</Btn>
        </footer>
      </div>
    </Scrim>
  )
}

function TrashSection({ titleKey, items, getName, getDate, onRestore, restoreLabelKey }) {
  const { t } = useTranslation('trash')
  if (items.length === 0) return null
  return (
    <section className="sun-trash-section" aria-labelledby={`trash-${titleKey}`}>
      <h2 id={`trash-${titleKey}`} className="sun-trash-section__title">{t(`sections.${titleKey}`)}</h2>
      <ul className="sun-trash-list">
        {items.map((item) => {
          const name = getName(item) || t('untitled')
          return (
            <li key={item.id} className="sun-trash-item">
              <div className="sun-trash-item__body">
                <span className="sun-trash-item__name">{name}</span>
                {getDate(item) && (
                  <span className="sun-trash-item__meta">{t('deletedAt', { date: dateTime(getDate(item)) })}</span>
                )}
              </div>
              <Btn
                variant="secondary"
                size="sm"
                icon="rotate-ccw"
                aria-label={t(restoreLabelKey, { name })}
                onClick={() => onRestore(item)}
              >
                {t('restore')}
              </Btn>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export default function Trash() {
  const { t } = useTranslation('trash')
  const { can } = useAuth()
  const canProjects = can('project:delete')
  const canCatalogs = can('catalog:manage')
  const [projects, setProjects] = useState([])
  const [catalogs, setCatalogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pending, setPending] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [p, c] = await Promise.all([
        canProjects ? api.projects.listDeleted() : Promise.resolve([]),
        canCatalogs ? api.catalogs.listDeleted() : Promise.resolve([]),
      ])
      setProjects(p)
      setCatalogs(c)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [canProjects, canCatalogs])

  useEffect(() => {
    load()
  }, [load])

  async function confirmRestore() {
    const { kind, item } = pending
    setPending(null)
    try {
      if (kind === 'project') await api.projects.restore(item.id)
      else await api.catalogs.restore(item.id)
      toast('success', t('restored'))
      await load()
    } catch (e) {
      toast('error', t('restoreError'), e.message)
    }
  }

  const isEmpty = projects.length === 0 && catalogs.length === 0

  return (
    <>
      <Topbar title={t('title')} />
      <Card className="sun-card--pad">
        <p className="sun-trash__subtitle">{t('subtitle')}</p>
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : loading ? (
          <Spinner />
        ) : isEmpty ? (
          <div className="sun-empty">
            <div className="sun-empty__icon"><Icon name="trash-2" size={26} /></div>
            <div className="sun-empty__desc">{t('empty')}</div>
          </div>
        ) : (
          <>
            <TrashSection
              titleKey="projects"
              items={projects}
              getName={(p) => p.cliente}
              getDate={(p) => p.deleted_at}
              restoreLabelKey="restoreProject"
              onRestore={(item) => setPending({ kind: 'project', item })}
            />
            <TrashSection
              titleKey="catalogs"
              items={catalogs}
              getName={(c) => c.nombre}
              getDate={(c) => c.deleted_at}
              restoreLabelKey="restoreCatalog"
              onRestore={(item) => setPending({ kind: 'catalog', item })}
            />
          </>
        )}
      </Card>
      {pending && (
        <ConfirmRestore
          kind={pending.kind}
          name={(pending.kind === 'project' ? pending.item.cliente : pending.item.nombre) || t('untitled')}
          onCancel={() => setPending(null)}
          onConfirm={confirmRestore}
        />
      )}
    </>
  )
}

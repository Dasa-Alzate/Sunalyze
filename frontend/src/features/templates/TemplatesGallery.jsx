import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Topbar, Btn, IconBtn, Icon, Badge, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { kindLabel, STATUS_TONES } from './constants'
import CreateTemplateDialog from './CreateTemplateDialog'

const TABS = [
  { key: 'bank', label: 'Banco', icon: 'library' },
  { key: 'org', label: 'Mis plantillas', icon: 'folder' },
  { key: 'library', label: 'Biblioteca', icon: 'bookmark' },
]

function TemplateCard({ template, installation, onOpen, onInstall, onUninstall, onFavorite }) {
  const statusTone = STATUS_TONES[template.status] || STATUS_TONES.draft
  return (
    <div className="sun-card module-card">
      <div className="module-card__body">
        <div className="module-card__head">
          <strong className="module-card__title">{template.name}</strong>
          {installation && (
            <IconBtn
              icon={installation.is_favorite ? 'star' : 'star'}
              label={installation.is_favorite ? 'Quitar de favoritos' : 'Marcar favorito'}
              size="sm"
              aria-pressed={installation.is_favorite}
              onClick={() => onFavorite(installation)}
              style={installation.is_favorite ? { color: 'var(--state-warn)' } : undefined}
            />
          )}
        </div>
        <p className="module-card__desc">{template.description || 'Sin descripción.'}</p>
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', marginBottom: 'var(--space-2)' }}>
          <Badge tone="neutral">{kindLabel(template.kind)}</Badge>
          {template.is_system ? <Badge tone="neutral" icon="shield">Oficial</Badge> : <Badge tone={statusTone.tone}>{statusTone.label}</Badge>}
          {(installation?.labels || []).map((l) => <Badge key={l.id} tone="neutral" icon="tag">{l.name}</Badge>)}
        </div>
        <div className="module-card__foot">
          {!template.is_system && (
            <Btn variant="secondary" size="sm" icon="pencil" onClick={() => onOpen(template)}>Editar</Btn>
          )}
          {installation ? (
            <Btn variant="secondary" size="sm" icon="x" onClick={() => onUninstall(installation)}>Quitar de la selección</Btn>
          ) : (
            <Btn variant="primary" size="sm" icon="plus" onClick={() => onInstall(template)}>Instalar</Btn>
          )}
        </div>
      </div>
    </div>
  )
}

export default function TemplatesGallery() {
  const nav = useNavigate()
  const [tab, setTab] = useState('bank')
  const [bank, setBank] = useState(null)
  const [orgTemplates, setOrgTemplates] = useState(null)
  const [library, setLibrary] = useState(null)
  const [categories, setCategories] = useState([])
  const [labels, setLabels] = useState([])
  const [error, setError] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [labelFilter, setLabelFilter] = useState('')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [creating, setCreating] = useState(false)

  function loadLibrary() {
    return api.templates.library({ favorite: favoritesOnly || undefined, categoryId: categoryFilter || undefined })
      .then(setLibrary)
  }

  function loadAll() {
    setError(null)
    Promise.all([
      api.templates.bank().then(setBank),
      api.templates.list().then(setOrgTemplates),
      api.templates.categories().then(setCategories),
      api.templates.labels().then(setLabels),
      loadLibrary(),
    ]).catch((e) => setError(e.message))
  }
  useEffect(loadAll, [])
  useEffect(() => { loadLibrary().catch((e) => setError(e.message)) }, [favoritesOnly, categoryFilter])

  const installedByTemplate = useMemo(() => {
    const map = {}
    ;(library || []).forEach((inst) => { map[inst.template_id] = inst })
    return map
  }, [library])

  function open(template) { nav(`/app/plantillas/${template.id}`) }

  async function install(template) {
    try {
      await api.templates.install(template.id)
      toast('success', 'Plantilla instalada', template.name)
      loadLibrary()
    } catch (e) { toast('error', 'No se pudo instalar', e.message) }
  }

  async function uninstall(installation) {
    try {
      await api.templates.uninstall(installation.id)
      toast('info', 'Quitada de la selección')
      loadLibrary()
    } catch (e) { toast('error', 'No se pudo quitar', e.message) }
  }

  async function favorite(installation) {
    try {
      await api.templates.setFavorite(installation.id, !installation.is_favorite)
      loadLibrary()
    } catch (e) { toast('error', 'No se pudo actualizar', e.message) }
  }

  function onCreated(tpl) { setCreating(false); nav(`/app/plantillas/${tpl.id}`) }

  const libraryFiltered = useMemo(() => {
    let rows = library || []
    if (labelFilter) rows = rows.filter((i) => (i.labels || []).some((l) => String(l.id) === labelFilter))
    return rows
  }, [library, labelFilter])

  function renderGrid(list, asInstallations) {
    if (list === null) return <Spinner label="Cargando plantillas…" />
    if (list.length === 0) {
      return (
        <div className="sun-empty">
          <div className="sun-empty__icon"><Icon name="file-text" size={26} /></div>
          <div className="sun-empty__title">Sin plantillas</div>
          <div className="sun-empty__desc">No hay plantillas que mostrar aquí todavía.</div>
        </div>
      )
    }
    return (
      <div className="catalog-grid">
        {list.map((row) => {
          const template = asInstallations ? row.template : row
          const installation = asInstallations ? row : installedByTemplate[row.id]
          if (!template) return null
          return (
            <TemplateCard
              key={asInstallations ? `inst-${row.id}` : `tpl-${row.id}`}
              template={template}
              installation={installation}
              onOpen={open}
              onInstall={install}
              onUninstall={uninstall}
              onFavorite={favorite}
            />
          )
        })}
      </div>
    )
  }

  return (
    <>
      <Topbar
        title="Plantillas de documentos"
        crumb="Documentos"
        actions={<Btn variant="primary" icon="plus" onClick={() => setCreating(true)}>Nueva plantilla</Btn>}
      />
      <div className="sun-content">
        {error ? (
          <ErrorState message={error} onRetry={loadAll} />
        ) : (
          <>
            <div className="sun-tabs" role="tablist" aria-label="Vistas de plantillas">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  role="tab"
                  aria-selected={tab === t.key}
                  className={`sun-tab${tab === t.key ? ' sun-tab--active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  <Icon name={t.icon} size={16} />{t.label}
                </button>
              ))}
            </div>

            {tab === 'library' && (
              <div className="sun-toolbar" style={{ marginTop: 'var(--space-4)' }}>
                <label className="sun-field__label" htmlFor="tpl-cat">Categoría</label>
                <select id="tpl-cat" className="sun-select" style={{ width: 180 }} value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
                  <option value="">Todas</option>
                  {categories.map((c) => <option key={c.id} value={String(c.id)}>{c.name}</option>)}
                </select>
                <label className="sun-field__label" htmlFor="tpl-label">Etiqueta</label>
                <select id="tpl-label" className="sun-select" style={{ width: 180 }} value={labelFilter} onChange={(e) => setLabelFilter(e.target.value)}>
                  <option value="">Todas</option>
                  {labels.map((l) => <option key={l.id} value={String(l.id)}>{l.name}</option>)}
                </select>
                <Btn
                  variant={favoritesOnly ? 'primary' : 'secondary'}
                  size="sm"
                  icon="star"
                  aria-pressed={favoritesOnly}
                  onClick={() => setFavoritesOnly((v) => !v)}
                >
                  Favoritos
                </Btn>
              </div>
            )}

            <div style={{ marginTop: 'var(--space-4)' }}>
              {tab === 'bank' && renderGrid(bank, false)}
              {tab === 'org' && renderGrid(orgTemplates, false)}
              {tab === 'library' && renderGrid(library === null ? null : libraryFiltered, true)}
            </div>
          </>
        )}
      </div>
      {creating && <CreateTemplateDialog onCreated={onCreated} onClose={() => setCreating(false)} />}
    </>
  )
}

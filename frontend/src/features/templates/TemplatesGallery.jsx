import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Topbar, Btn, IconBtn, Icon, Badge, Spinner, ErrorState } from '@/shared/ui'
import { api } from '@/api/client'
import { toast } from '@/services/toast'
import { kindLabel, stageLabel, TEMPLATE_STAGES, STATUS_TONES } from './constants'
import CreateTemplateDialog from './CreateTemplateDialog'
import AssignTemplateDialog from './AssignTemplateDialog'

const TABS = [
  { key: 'bank', label: 'Banco', icon: 'library' },
  { key: 'org', label: 'Mis plantillas', icon: 'folder' },
  { key: 'library', label: 'Biblioteca', icon: 'bookmark' },
]

function TemplateCard({ template, installation, kinds, onOpen, onInstall, onUninstall, onFavorite, onOrganize }) {
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
          <Badge tone="neutral">{kindLabel(template.kind, kinds)}</Badge>
          {template.is_system ? <Badge tone="neutral" icon="shield">Oficial</Badge> : <Badge tone={statusTone.tone}>{statusTone.label}</Badge>}
          {template.stage && <Badge tone="info" icon="git-branch">{stageLabel(template.stage)}</Badge>}
          {template.country && <Badge tone="neutral" icon="map-pin">{template.country}</Badge>}
          {template.required_by && <Badge tone="neutral" icon="landmark">{template.required_by}</Badge>}
          {(installation?.labels || []).map((l) => <Badge key={l.id} tone="neutral" icon="tag">{l.name}</Badge>)}
        </div>
        <div className="module-card__foot">
          {!template.is_system && (
            <Btn variant="secondary" size="sm" icon="pencil" onClick={() => onOpen(template)}>Editar</Btn>
          )}
          {installation ? (
            <>
              <Btn variant="secondary" size="sm" icon="tag" onClick={() => onOrganize(installation)}>Organizar</Btn>
              <Btn variant="secondary" size="sm" icon="x" onClick={() => onUninstall(installation)}>Quitar de la selección</Btn>
            </>
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
  const { t } = useTranslation('templates')
  const [tab, setTab] = useState('bank')
  const [bank, setBank] = useState(null)
  const [orgTemplates, setOrgTemplates] = useState(null)
  const [library, setLibrary] = useState(null)
  const [categories, setCategories] = useState([])
  const [labels, setLabels] = useState([])
  const [kinds, setKinds] = useState([])
  const [error, setError] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [labelFilter, setLabelFilter] = useState('')
  const [kindFilter, setKindFilter] = useState([])
  const [stageFilter, setStageFilter] = useState('')
  const [countryFilter, setCountryFilter] = useState('')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [creating, setCreating] = useState(false)
  const [organizing, setOrganizing] = useState(null)

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
      api.templates.kinds().then((rows) => setKinds((rows || []).map((r) => ({ value: r.key, label: r.label })))),
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

  function refreshTaxonomy() {
    Promise.all([
      api.templates.categories().then(setCategories),
      api.templates.labels().then(setLabels),
    ]).catch((e) => setError(e.message))
  }

  function onOrganized() {
    setOrganizing(null)
    refreshTaxonomy()
    loadLibrary().catch((e) => setError(e.message))
  }

  function toggleKind(value) {
    setKindFilter((prev) => (prev.includes(value) ? prev.filter((k) => k !== value) : [...prev, value]))
  }

  function matchesTags(template) {
    if (!template) return false
    if (kindFilter.length && !kindFilter.includes(template.kind)) return false
    if (stageFilter && template.stage !== stageFilter) return false
    if (countryFilter && template.country !== countryFilter) return false
    return true
  }

  const countryOptions = useMemo(() => {
    const all = [...(bank || []), ...(orgTemplates || []), ...((library || []).map((i) => i.template).filter(Boolean))]
    const set = new Set(all.map((t2) => t2.country).filter(Boolean))
    return [...set].sort()
  }, [bank, orgTemplates, library])

  const bankFiltered = useMemo(() => (bank || []).filter(matchesTags), [bank, kindFilter, stageFilter, countryFilter])
  const orgFiltered = useMemo(() => (orgTemplates || []).filter(matchesTags), [orgTemplates, kindFilter, stageFilter, countryFilter])

  const libraryFiltered = useMemo(() => {
    let rows = library || []
    if (labelFilter) rows = rows.filter((i) => (i.labels || []).some((l) => String(l.id) === labelFilter))
    rows = rows.filter((i) => matchesTags(i.template))
    return rows
  }, [library, labelFilter, kindFilter, stageFilter, countryFilter])

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
              kinds={kinds}
              onOpen={open}
              onInstall={install}
              onUninstall={uninstall}
              onFavorite={favorite}
              onOrganize={setOrganizing}
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

            <div className="sun-toolbar" style={{ marginTop: 'var(--space-4)' }}>
              <label className="sun-field__label" htmlFor="tpl-stage">{t('filters.stage')}</label>
              <select id="tpl-stage" className="sun-select" style={{ width: 180 }} value={stageFilter} onChange={(e) => setStageFilter(e.target.value)}>
                <option value="">{t('filters.all')}</option>
                {TEMPLATE_STAGES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <label className="sun-field__label" htmlFor="tpl-country">{t('filters.country')}</label>
              <select id="tpl-country" className="sun-select" style={{ width: 180 }} value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)}>
                <option value="">{t('filters.allCountries')}</option>
                {countryOptions.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {kinds.length > 0 && (
              <div className="sun-toolbar tpl-kind-filter" style={{ marginTop: 'var(--space-4)' }}>
                <span className="sun-field__label">Tipo de documento</span>
                <div className="tpl-kind-filter__chips" role="group" aria-label="Filtrar por tipo de documento">
                  {kinds.map((k) => (
                    <Btn
                      key={k.value}
                      variant={kindFilter.includes(k.value) ? 'primary' : 'secondary'}
                      size="sm"
                      aria-pressed={kindFilter.includes(k.value)}
                      onClick={() => toggleKind(k.value)}
                    >
                      {k.label}
                    </Btn>
                  ))}
                  {kindFilter.length > 0 && (
                    <Btn variant="ghost" size="sm" icon="x" onClick={() => setKindFilter([])}>Limpiar</Btn>
                  )}
                </div>
              </div>
            )}

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
              {tab === 'bank' && renderGrid(bank === null ? null : bankFiltered, false)}
              {tab === 'org' && renderGrid(orgTemplates === null ? null : orgFiltered, false)}
              {tab === 'library' && renderGrid(library === null ? null : libraryFiltered, true)}
            </div>
          </>
        )}
      </div>
      {creating && <CreateTemplateDialog onCreated={onCreated} onClose={() => setCreating(false)} />}
      {organizing && (
        <AssignTemplateDialog
          installation={organizing}
          categories={categories}
          labels={labels}
          onClose={() => setOrganizing(null)}
          onSaved={onOrganized}
        />
      )}
    </>
  )
}

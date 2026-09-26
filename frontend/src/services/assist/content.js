let artifactPromise = null

export function loadHelp() {
  artifactPromise ??= import('@/generated/help-articles.json').then((m) => m.default || m)
  return artifactPromise
}

export function resolveLocale(data, language) {
  const short = String(language || '').slice(0, 2).toLowerCase()
  return data.locales[short] ? short : data.baseLocale
}

export function effectiveArticles(data, locale) {
  const base = data.locales[data.baseLocale] || []
  if (locale === data.baseLocale) {
    return base.filter((a) => a.status === 'published').map((a) => ({ article: a, fellBack: false }))
  }
  const translated = new Map((data.locales[locale] || []).map((a) => [a.slug, a]))
  return base
    .filter((a) => a.status === 'published')
    .map((baseArticle) => {
      const tr = translated.get(baseArticle.slug)
      if (tr && !tr.stale && tr.status === 'published') return { article: tr, fellBack: false }
      return { article: baseArticle, fellBack: true }
    })
}

export function articleForContext(entries, view, subview) {
  const scored = entries
    .map((entry) => {
      const routes = entry.article.routes || []
      const exact = subview && routes.some((r) => r.view === view && r.subview === subview)
      const viewLevel = routes.some((r) => r.view === view && !r.subview)
      if (exact) return { entry, score: 2 }
      if (viewLevel) return { entry, score: 1 }
      return null
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || a.entry.article.order - b.entry.article.order)
  return scored.length ? scored[0].entry : null
}

export function relatedArticles(entries, view, exceptSlug) {
  return entries
    .filter(({ article }) => article.slug !== exceptSlug && (article.routes || []).some((r) => r.view === view))
    .map(({ article }) => article)
}

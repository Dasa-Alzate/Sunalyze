import { Index } from 'flexsearch'

function fold(text) {
  return String(text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

export function createSearchAdapter(entries) {
  const index = new Index({ tokenize: 'forward' })
  entries.forEach(({ article }, i) => {
    index.add(i, fold(`${article.title} ${(article.keywords || []).join(' ')} ${article.search}`))
  })
  return {
    query(text, limit = 8) {
      const q = fold(text).trim()
      if (q.length < 2) return []
      return index.search(q, limit).map((i) => entries[i])
    },
  }
}

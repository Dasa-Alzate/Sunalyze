import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { parseArticle, searchText, ParseError } from './parse.mjs'

const HERE = path.dirname(fileURLToPath(import.meta.url))
export const ROOT = path.resolve(HERE, '../../..')
export const DOCS = path.join(ROOT, 'docs', 'help')
export const SHOTS = path.join(DOCS, 'screenshots')
const OUT_DIR = path.join(ROOT, 'frontend', 'src', 'generated')
const OUT_FILE = path.join(OUT_DIR, 'help-articles.json')
const PUBLIC_SHOTS = path.join(ROOT, 'frontend', 'public', 'help')

export const LOCALES = ['es', 'en']
const BASE_LOCALE = 'es'
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const SAFE_SRC = /^[a-z0-9][a-z0-9/_-]*\.(png|jpg|jpeg|webp)$/

export function contentHash(source) {
  const body = source.replace(/^---\n[\s\S]*?\n---\n?/, '')
  return createHash('sha1').update(body.trim()).digest('hex').slice(0, 12)
}

function surfaceVocabulary() {
  return JSON.parse(fs.readFileSync(path.join(DOCS, 'surfaces.json'), 'utf8'))
}

function listArticles(locale) {
  const dir = path.join(DOCS, locale)
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir).filter((f) => f.endsWith('.md')).sort()
}

function validateMeta(meta, file, surfaces, errors) {
  if (!meta.title || typeof meta.title !== 'string') errors.push(`${file}: falta «title» en el frontmatter`)
  if (meta.status && !['draft', 'published'].includes(meta.status)) {
    errors.push(`${file}: status «${meta.status}» inválido (draft | published)`)
  }
  if (meta.order !== undefined && !Number.isInteger(meta.order)) errors.push(`${file}: «order» debe ser entero`)
  const routes = []
  for (const raw of meta.routes || []) {
    const [view, subview] = String(raw).split('/')
    if (!(view in surfaces)) {
      errors.push(`${file}: ruta «${raw}» apunta a una vista desconocida (ver docs/help/surfaces.json)`)
    } else if (subview && !surfaces[view].includes(subview)) {
      errors.push(`${file}: ruta «${raw}» apunta a una subvista desconocida de «${view}» (admite: ${surfaces[view].join(', ') || 'ninguna'})`)
    } else {
      routes.push({ view, subview: subview || null })
    }
  }
  return routes
}

function collectShots(tabs) {
  const srcs = []
  for (const blocks of Object.values(tabs)) {
    for (const b of blocks) if (b.kind === 'screenshot') srcs.push(b.src)
  }
  return srcs
}

export function buildHelp({ log = () => {} } = {}) {
  const errors = []
  const warnings = []
  const surfaces = surfaceVocabulary()
  const locales = {}
  const baseHashes = {}

  for (const locale of LOCALES) {
    const articles = []
    for (const fileName of listArticles(locale)) {
      const rel = `docs/help/${locale}/${fileName}`
      const slug = fileName.replace(/\.md$/, '')
      if (!SLUG.test(slug)) {
        errors.push(`${rel}: el nombre del fichero debe ser un slug (minúsculas, números, guiones)`)
        continue
      }
      const source = fs.readFileSync(path.join(DOCS, locale, fileName), 'utf8')
      let parsed
      try {
        parsed = parseArticle(source, rel)
      } catch (err) {
        if (err instanceof ParseError) { errors.push(err.message); continue }
        throw err
      }
      const routes = validateMeta(parsed.meta, rel, surfaces, errors)
      for (const src of collectShots(parsed.tabs)) {
        if (!SAFE_SRC.test(src)) {
          errors.push(`${rel}: src de captura inválido «${src}» (ruta relativa segura .png/.jpg/.webp)`)
        } else if (!fs.existsSync(path.join(SHOTS, src))) {
          warnings.push(`${rel}: captura ausente «${src}» (corre npm run help:shots o añádela a docs/help/screenshots/)`)
        }
      }
      if (locale === BASE_LOCALE) baseHashes[slug] = contentHash(source)
      const article = {
        slug,
        title: parsed.meta.title || slug,
        status: parsed.meta.status || 'published',
        order: parsed.meta.order ?? 100,
        routes,
        keywords: (parsed.meta.keywords || []).map(String),
        tabs: parsed.tabs,
        search: searchText(parsed.tabs),
      }
      if (locale !== BASE_LOCALE) {
        article.sourceHash = parsed.meta.source_hash || null
      }
      articles.push(article)
    }
    articles.sort((a, b) => a.order - b.order || a.slug.localeCompare(b.slug))
    locales[locale] = articles
  }

  for (const locale of LOCALES) {
    if (locale === BASE_LOCALE) continue
    for (const article of locales[locale]) {
      if (!(article.slug in baseHashes)) {
        warnings.push(`docs/help/${locale}/${article.slug}.md: no existe el original ${BASE_LOCALE} (huérfano de traducción)`)
        article.stale = true
      } else if (article.sourceHash !== baseHashes[article.slug]) {
        warnings.push(`docs/help/${locale}/${article.slug}.md: desfasado respecto al ${BASE_LOCALE} (corre npm run help:stamp tras retraducir)`)
        article.stale = true
      } else {
        article.stale = false
      }
      delete article.sourceHash
    }
  }

  const published = locales[BASE_LOCALE].filter((a) => a.status === 'published')
  const slots = {}
  for (const article of published) {
    for (const r of article.routes) {
      const key = `${r.view}/${r.subview || ''}`
      ;(slots[key] = slots[key] || []).push(article.slug)
    }
  }
  for (const [slot, slugs] of Object.entries(slots)) {
    if (slugs.length > 1) warnings.push(`slot «${slot}» cubierto por varios artículos publicados: ${slugs.join(', ')} (gana el de menor order)`)
  }
  for (const [view, subviews] of Object.entries(surfaces)) {
    for (const key of [view + '/', ...subviews.map((s) => `${view}/${s}`)]) {
      if (!(key in slots)) warnings.push(`slot «${key.replace(/\/$/, '')}» sin artículo publicado`)
    }
  }

  if (errors.length) {
    const err = new Error(['El contenido de ayuda no compila:', ...errors.map((e) => '  ✗ ' + e)].join('\n'))
    err.helpErrors = errors
    throw err
  }

  fs.mkdirSync(OUT_DIR, { recursive: true })
  const artifact = {
    version: 1,
    baseLocale: BASE_LOCALE,
    locales,
  }
  fs.writeFileSync(OUT_FILE, JSON.stringify(artifact))

  fs.rmSync(PUBLIC_SHOTS, { recursive: true, force: true })
  if (fs.existsSync(SHOTS)) {
    fs.cpSync(SHOTS, PUBLIC_SHOTS, { recursive: true })
  }

  log(`help: ${locales.es.length} artículos es, ${locales.en.length} en → src/generated/help-articles.json`)
  for (const w of warnings) log('  ⚠ ' + w)
  return { warnings, artifact }
}

const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (invoked) {
  try {
    const { warnings } = buildHelp({ log: console.log })
    if (process.argv.includes('--strict') && warnings.length) process.exit(2)
  } catch (err) {
    console.error(err.message)
    process.exit(1)
  }
}

import matter from 'gray-matter'
import { marked } from 'marked'

export const TABS = ['concepto', 'criterio', 'flujo', 'tutorial']
export const TONES = ['info', 'success', 'warning', 'danger', 'brand', 'purple']

export const DIRECTIVES = {
  tip: { attrs: ['tone', 'title'], body: 'markdown' },
  callout: { attrs: ['tone'], body: 'markdown' },
  steps: { attrs: [], body: 'items' },
  cards: { attrs: [], body: 'items' },
  flow: { attrs: [], body: 'items' },
  norm: { attrs: ['code'], body: 'markdown' },
  screenshot: { attrs: ['src', 'alt'], body: 'markdown' },
}

marked.setOptions({ gfm: true, breaks: false })

const OPEN = /^:::([a-z]+)(?:\{([^}]*)\})?\s*$/
const CLOSE = /^:::\s*$/
const ATTR = /([a-z_]+)=(?:"([^"]*)"|([^\s"]+))/g

export class ParseError extends Error {
  constructor(file, line, message) {
    super(`${file}:${line}: ${message}`)
    this.file = file
    this.line = line
    this.reason = message
  }
}

function parseAttrs(raw, allowed, file, line) {
  const attrs = {}
  if (!raw) return attrs
  let m
  while ((m = ATTR.exec(raw)) !== null) {
    const key = m[1]
    if (!allowed.includes(key)) {
      throw new ParseError(file, line, `atributo «${key}» no permitido (admite: ${allowed.join(', ') || 'ninguno'})`)
    }
    attrs[key] = m[2] !== undefined ? m[2] : m[3]
  }
  if (attrs.tone && !TONES.includes(attrs.tone)) {
    throw new ParseError(file, line, `tone «${attrs.tone}» inválido (admite: ${TONES.join(', ')})`)
  }
  return attrs
}

function parseItems(lines, file, startLine) {
  const items = []
  let current = null
  for (const line of lines) {
    const m = line.match(/^(?:[-*]|\d+[.)])\s+(.*)$/)
    if (m) {
      if (current !== null) items.push(current)
      current = m[1]
    } else if (current !== null && line.trim()) {
      current += ' ' + line.trim()
    } else if (line.trim()) {
      throw new ParseError(file, startLine, `contenido fuera de un ítem de lista: «${line.trim().slice(0, 40)}»`)
    }
  }
  if (current !== null) items.push(current)
  return items.map((item) => {
    const split = item.match(/^\*\*(.+?)\*\*\s*(?:[—:-]\s*)?(.*)$/)
    if (split) return { title: split[1], body: marked.parseInline(split[2] || '') }
    return { title: null, body: marked.parseInline(item) }
  })
}

function flushProse(buffer, blocks) {
  const text = buffer.join('\n').trim()
  buffer.length = 0
  if (text) blocks.push({ kind: 'prose', html: marked.parse(text) })
}

function directiveBlock(kind, attrs, bodyLines, file, line) {
  const spec = DIRECTIVES[kind]
  const block = { kind, ...attrs }
  if (spec.body === 'items') {
    block.items = parseItems(bodyLines, file, line)
    if (!block.items.length) throw new ParseError(file, line, `«${kind}» requiere al menos un ítem de lista`)
  } else {
    const body = bodyLines.join('\n').trim()
    if (kind === 'screenshot') {
      if (!attrs.src) throw new ParseError(file, line, 'screenshot requiere src=')
      if (body) block.caption = marked.parseInline(body)
    } else {
      if (!body) throw new ParseError(file, line, `«${kind}» requiere cuerpo`)
      block.body = marked.parse(body)
    }
  }
  return block
}

export function parseArticle(source, file) {
  let fm
  try {
    fm = matter(source)
  } catch (err) {
    throw new ParseError(file, 1, `frontmatter inválido: ${err.message}`)
  }
  const meta = fm.data || {}
  const lines = fm.content.split('\n')
  const fmOffset = source.slice(0, source.indexOf(fm.content)).split('\n').length - 1

  const tabs = {}
  let tab = null
  let blocks = null
  const prose = []
  let directive = null

  lines.forEach((line, i) => {
    const n = i + 1 + fmOffset

    if (directive) {
      if (CLOSE.test(line)) {
        blocks.push(directiveBlock(directive.kind, directive.attrs, directive.body, file, directive.line))
        directive = null
      } else {
        directive.body.push(line)
      }
      return
    }

    const open = line.match(OPEN)
    if (open) {
      if (!DIRECTIVES[open[1]]) throw new ParseError(file, n, `directiva desconocida «:::${open[1]}» (admite: ${Object.keys(DIRECTIVES).join(', ')})`)
      if (!tab) throw new ParseError(file, n, 'contenido antes de la primera pestaña (# Concepto, # Criterio, # Flujo o # Tutorial)')
      flushProse(prose, blocks)
      directive = { kind: open[1], attrs: parseAttrs(open[2], DIRECTIVES[open[1]].attrs, file, n), body: [], line: n }
      return
    }

    const h1 = line.match(/^#\s+(.+?)\s*$/)
    if (h1) {
      const name = h1[1].toLowerCase()
      if (!TABS.includes(name)) throw new ParseError(file, n, `pestaña «${h1[1]}» desconocida (admite: ${TABS.map((t) => t[0].toUpperCase() + t.slice(1)).join(', ')})`)
      if (tabs[name]) throw new ParseError(file, n, `pestaña «${h1[1]}» duplicada`)
      if (tab) flushProse(prose, blocks)
      tab = name
      blocks = []
      tabs[name] = blocks
      return
    }

    const h2 = line.match(/^##\s+(.+?)\s*$/)
    if (h2) {
      if (!tab) throw new ParseError(file, n, 'sección antes de la primera pestaña')
      flushProse(prose, blocks)
      blocks.push({ kind: 'section', title: h2[1] })
      return
    }

    if (!tab) {
      if (line.trim()) throw new ParseError(file, n, 'contenido antes de la primera pestaña (# Concepto, # Criterio, # Flujo o # Tutorial)')
      return
    }
    prose.push(line)
  })

  if (directive) throw new ParseError(file, directive.line, `directiva «:::${directive.kind}» sin cerrar (falta «:::»)`)
  if (tab) flushProse(prose, blocks)
  if (!Object.keys(tabs).length) throw new ParseError(file, 1, 'el artículo no tiene ninguna pestaña (# Concepto, # Criterio, # Flujo o # Tutorial)')

  return { meta, tabs, raw: fm.content }
}

export function searchText(tabs) {
  const parts = []
  for (const blocks of Object.values(tabs)) {
    for (const b of blocks) {
      for (const v of [b.title, b.html, b.body, b.caption]) {
        if (v) parts.push(String(v).replace(/<[^>]+>/g, ' '))
      }
      for (const item of b.items || []) {
        if (item.title) parts.push(item.title)
        if (item.body) parts.push(String(item.body).replace(/<[^>]+>/g, ' '))
      }
    }
  }
  return parts.join(' ').replace(/\s+/g, ' ').trim()
}

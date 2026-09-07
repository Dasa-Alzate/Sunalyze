import fs from 'node:fs'
import path from 'node:path'

import { DOCS, LOCALES, contentHash } from './build.mjs'

const BASE = 'es'
const targets = LOCALES.filter((l) => l !== BASE)
const only = process.argv.slice(2).map((f) => path.basename(f, '.md'))

let stamped = 0
for (const locale of targets) {
  const dir = path.join(DOCS, locale)
  if (!fs.existsSync(dir)) continue
  for (const fileName of fs.readdirSync(dir).filter((f) => f.endsWith('.md'))) {
    const slug = fileName.replace(/\.md$/, '')
    if (only.length && !only.includes(slug)) continue
    const basePath = path.join(DOCS, BASE, fileName)
    if (!fs.existsSync(basePath)) {
      console.warn(`⚠ ${locale}/${fileName}: sin original ${BASE}, no se sella`)
      continue
    }
    const hash = contentHash(fs.readFileSync(basePath, 'utf8'))
    const file = path.join(dir, fileName)
    let source = fs.readFileSync(file, 'utf8')
    if (/^---\n[\s\S]*?\n---/.test(source)) {
      source = /source_hash:/.test(source)
        ? source.replace(/source_hash:.*/, `source_hash: ${hash}`)
        : source.replace(/^---\n/, `---\nsource_hash: ${hash}\n`)
    } else {
      source = `---\nsource_hash: ${hash}\n---\n` + source
    }
    fs.writeFileSync(file, source)
    stamped += 1
    console.log(`✓ ${locale}/${fileName} → ${hash}`)
  }
}
console.log(`${stamped} traducciones selladas.`)

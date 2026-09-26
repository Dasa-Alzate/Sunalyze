import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { chromium } from 'playwright'
import { DOCS, SHOTS } from './build.mjs'

const MANIFEST = path.join(DOCS, 'screens.json')
const SAFE_SRC = /^[a-z0-9][a-z0-9_-]*(\/[a-z0-9][a-z0-9_-]*)*\.png$/

function fail(message) {
  console.error(`✗ help:shots — ${message}`)
  process.exit(1)
}

function subst(value) {
  return value.replace(/\$\{([A-Z0-9_]+)\}/g, (_, name) => {
    const v = process.env[name]
    if (v === undefined) throw new Error(`la variable de entorno ${name} no está definida`)
    return v
  })
}

async function runSteps(page, steps) {
  for (const step of steps || []) {
    if (step.click) await page.click(subst(step.click))
    else if (step.fill) await page.fill(subst(step.fill[0]), subst(step.fill[1]))
    else if (step.waitFor) await page.waitForSelector(subst(step.waitFor))
    else if (step.pause) await page.waitForTimeout(step.pause)
    else throw new Error(`paso desconocido: ${JSON.stringify(step)} (admite: click, fill, waitFor, pause)`)
  }
}

if (!fs.existsSync(MANIFEST)) {
  console.log('help:shots — no existe docs/help/screens.json; captura automática desactivada (suelta PNGs a mano en docs/help/screenshots/).')
  process.exit(0)
}

let manifest
try {
  manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'))
} catch (err) {
  fail(`docs/help/screens.json no es JSON válido: ${err.message}`)
}

const onlyIdx = process.argv.indexOf('--only')
const only = onlyIdx !== -1 ? process.argv[onlyIdx + 1] : null
const baseUrl = (process.env.HELP_SHOTS_BASE || manifest.baseUrl || 'http://localhost:5173').replace(/\/$/, '')
const viewport = manifest.viewport || { width: 1440, height: 900 }
const shots = (manifest.shots || []).filter((s) => !only || s.src === only)

if (!shots.length) {
  console.log(only ? `help:shots — ninguna captura coincide con «${only}».` : 'help:shots — el manifest no declara capturas.')
  process.exit(0)
}

for (const shot of shots) {
  if (!shot.src || !SAFE_SRC.test(shot.src)) fail(`src inválido «${shot.src}» (minúsculas, dígitos, guiones y subcarpetas; extensión .png)`)
  if (!shot.path || !shot.path.startsWith('/')) fail(`«${shot.src}» necesita un path que empiece por / (tiene: ${shot.path})`)
}

let email = null
let password = null
if (manifest.login) {
  const userEnv = manifest.login.userEnv || 'HELP_SHOTS_EMAIL'
  const passEnv = manifest.login.passEnv || 'HELP_SHOTS_PASSWORD'
  email = process.env[userEnv]
  password = process.env[passEnv]
  if (!email || !password) fail(`el manifest pide login pero faltan credenciales: exporta ${userEnv} y ${passEnv}`)
}

console.log(`help:shots — ${shots.length} captura(s) contra ${baseUrl}`)

const browser = await chromium.launch()
const page = await browser.newPage({ viewport, locale: 'es-ES' })
page.setDefaultTimeout(manifest.timeout || 15000)

try {
  if (manifest.login) {
    await page.goto(baseUrl + (manifest.login.path || '/login'), { waitUntil: 'networkidle' })
    await page.fill('input[type="email"]', email)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.waitForURL(`**${manifest.login.expect || '/app'}**`)
  }
} catch (err) {
  await browser.close()
  fail(`el login falló: ${err.message.split('\n')[0]}`)
}

let failures = 0
for (const shot of shots) {
  try {
    await page.goto(baseUrl + subst(shot.path), { waitUntil: 'networkidle' })
    await runSteps(page, shot.steps)
    if (shot.waitFor) await page.waitForSelector(subst(shot.waitFor))
    const dest = path.join(SHOTS, shot.src)
    fs.mkdirSync(path.dirname(dest), { recursive: true })
    if (shot.selector) await page.locator(subst(shot.selector)).first().screenshot({ path: dest })
    else await page.screenshot({ path: dest, fullPage: Boolean(shot.fullPage) })
    console.log(`  ✓ ${shot.src}`)
  } catch (err) {
    failures += 1
    console.error(`  ✗ ${shot.src}: ${err.message.split('\n')[0]}`)
  }
}

await browser.close()

if (failures) {
  console.error(`help:shots — ${failures} captura(s) fallida(s).`)
  process.exit(1)
}
console.log(`help:shots — listo; PNGs en docs/help/screenshots/ (corre help:build para copiarlos al frontend).`)

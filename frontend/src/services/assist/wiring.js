import { createBus } from './bus'
import { attachClickEmitter, attachJsErrorEmitter, attachApiErrorEmitter, attachRageDetector } from './emitters'
import { attachRecorder, getSnapshot } from './recorder'
import { resolveView } from './context'

export const assistBus = createBus()

let wired = false
let teardowns = []

export function wireAssist() {
  if (wired) return
  wired = true
  teardowns = [
    attachRecorder(assistBus),
    attachClickEmitter(assistBus),
    attachJsErrorEmitter(assistBus),
    attachApiErrorEmitter(assistBus),
    attachRageDetector(assistBus),
  ]
}

export function unwireAssist() {
  teardowns.forEach((fn) => fn && fn())
  teardowns = []
  wired = false
}

export function emitView(pathname) {
  wireAssist()
  const view = resolveView(pathname)
  const snap = getSnapshot()
  if (snap.context.view === view && snap.context.path === pathname) return
  assistBus.emit('nav.view', { view, path: pathname })
}

export function emitSubview(view, subview) {
  wireAssist()
  const snap = getSnapshot()
  if (snap.context.view === view && snap.context.subview === subview) return
  assistBus.emit('nav.subview', { view, subview })
}

export { getSnapshot, resolveView }

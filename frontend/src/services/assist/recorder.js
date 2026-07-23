const KEY = 'sunalyze.assist'
const TRAIL_MAX = 50
const ERRORS_MAX = 10
const CLICK_KEYS_MAX = 40

function blank() {
  return {
    sid: Math.random().toString(36).slice(2, 10),
    context: { view: null, subview: null, path: null, since: Date.now() },
    trail: [],
    clicks: {},
    errors: [],
  }
}

function load() {
  try {
    const raw = sessionStorage.getItem(KEY)
    if (raw) return { ...blank(), ...JSON.parse(raw) }
  } catch { void 0 }
  return blank()
}

let state = null

function save() {
  try { sessionStorage.setItem(KEY, JSON.stringify(state)) } catch { void 0 }
}

export function getSnapshot() {
  if (!state) state = load()
  return state
}

export function attachRecorder(bus) {
  state = load()

  return bus.on('*', (event) => {
    state.trail.push({ t: event.t, type: event.type, data: event.data })
    if (state.trail.length > TRAIL_MAX) state.trail.splice(0, state.trail.length - TRAIL_MAX)

    if (event.type === 'nav.view') {
      const same = state.context.view === event.data.view
      state.context = {
        view: event.data.view,
        subview: same ? state.context.subview : null,
        path: event.data.path,
        since: same ? state.context.since : event.t,
      }
    } else if (event.type === 'nav.subview') {
      state.context = { ...state.context, view: event.data.view, subview: event.data.subview, since: event.t }
    } else if (event.type === 'dom.click') {
      const k = event.data.target
      state.clicks[k] = (state.clicks[k] || 0) + 1
      const keys = Object.keys(state.clicks)
      if (keys.length > CLICK_KEYS_MAX) {
        keys.sort((a, b) => state.clicks[a] - state.clicks[b])
        keys.slice(0, keys.length - CLICK_KEYS_MAX).forEach((k2) => delete state.clicks[k2])
      }
    } else if (event.type === 'api.error' || event.type === 'js.error') {
      state.errors.push({ t: event.t, type: event.type, ...event.data })
      if (state.errors.length > ERRORS_MAX) state.errors.splice(0, state.errors.length - ERRORS_MAX)
    }

    save()
  })
}

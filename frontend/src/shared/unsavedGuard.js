let guard = null

export function registerUnsavedGuard(g) {
  guard = g
  return () => { if (guard === g) guard = null }
}

export function getUnsavedGuard() {
  return guard
}

export function hasUnsavedChanges() {
  try { return Boolean(guard && guard.isDirty()) } catch { return false }
}

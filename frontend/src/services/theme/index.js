const KEY = 'sunalyze.theme'

let listeners = []

export function currentTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function subscribeTheme(fn) {
  listeners.push(fn)
  return () => {
    listeners = listeners.filter((l) => l !== fn)
  }
}

export function setTheme(theme) {
  document.documentElement.dataset.theme = theme
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    listeners.forEach((fn) => fn(theme))
    return theme
  }
  listeners.forEach((fn) => fn(theme))
  return theme
}

export function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark'
  setTheme(next)
  return next
}

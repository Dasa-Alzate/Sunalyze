const KEY = 'sunalyze.theme'

export function currentTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function setTheme(theme) {
  document.documentElement.dataset.theme = theme
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    return theme
  }
  return theme
}

export function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark'
  setTheme(next)
  return next
}

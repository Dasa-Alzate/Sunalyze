function scoreText(query, text) {
  const q = query.toLowerCase()
  const t = text.toLowerCase()
  let score = 0
  let qi = 0
  let prevIdx = -1
  for (let ti = 0; ti < t.length && qi < q.length; ti += 1) {
    if (t[ti] !== q[qi]) continue
    let gain = 1
    if (ti === prevIdx + 1) gain += 4
    if (ti === 0 || /[\s\-_/]/.test(t[ti - 1])) gain += 3
    gain += Math.max(0, 4 - ti)
    score += gain
    prevIdx = ti
    qi += 1
  }
  return qi === q.length ? score : -1
}

export function scoreAction(query, action) {
  const q = query.trim()
  if (!q) return 0
  let best = scoreText(q, action.label)
  for (const kw of action.keywords || []) {
    const s = scoreText(q, kw)
    if (s > best) best = s
  }
  return best
}

export function filterActions(query, actions) {
  const q = query.trim()
  if (!q) return actions
  return actions
    .map((action) => ({ action, score: scoreAction(q, action) }))
    .filter((r) => r.score >= 0)
    .sort((a, b) => b.score - a.score)
    .map((r) => r.action)
}

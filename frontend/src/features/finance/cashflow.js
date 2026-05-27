export function cumulativeSeries(results) {
  const cashflow = (results && results.cashflow) || []
  const initial = -(results?.capex?.initial_investment_eur ?? 0)
  const points = [{ year: 0, value: initial }]
  let running = initial
  cashflow.forEach((row) => {
    running += Number(row.cashflow_eur) || 0
    points.push({ year: row.year, value: running })
  })
  return points
}

export function paybackYear(points) {
  for (let i = 1; i < points.length; i += 1) {
    if (points[i - 1].value < 0 && points[i].value >= 0) return points[i].year
  }
  return null
}

export function buildChartGeometry(results, { width = 640, height = 280, pad = 40 } = {}) {
  const points = cumulativeSeries(results)
  if (points.length < 2) return null

  const values = points.map((p) => p.value)
  const minV = Math.min(0, ...values)
  const maxV = Math.max(0, ...values)
  const spanV = maxV - minV || 1
  const minYear = points[0].year
  const maxYear = points[points.length - 1].year
  const spanYear = maxYear - minYear || 1

  const x = (year) => pad + ((year - minYear) / spanYear) * (width - 2 * pad)
  const y = (value) => height - pad - ((value - minV) / spanV) * (height - 2 * pad)

  const coords = points.map((p) => ({ ...p, cx: x(p.year), cy: y(p.value) }))
  const line = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.cx.toFixed(1)},${c.cy.toFixed(1)}`).join(' ')
  const baseY = y(0)
  const area = `${line} L${coords[coords.length - 1].cx.toFixed(1)},${baseY.toFixed(1)} L${coords[0].cx.toFixed(1)},${baseY.toFixed(1)} Z`

  const pbYear = paybackYear(points)
  const paybackX = pbYear !== null ? x(pbYear) : null

  return {
    width,
    height,
    pad,
    points: coords,
    line,
    area,
    baseY,
    paybackX,
    paybackYear: pbYear,
    minYear,
    maxYear,
  }
}

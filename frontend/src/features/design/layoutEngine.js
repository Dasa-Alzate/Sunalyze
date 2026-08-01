const M_PER_DEG_LAT = 110574
const M_PER_DEG_LNG = 111320

const DEFAULT_GAP = 0.02
const OBLIQUITY = 23.45
const WINTER_DECLINATION = -OBLIQUITY
const SHADING_WINDOW_HOURS = 4
const SHADING_STEP_MIN = 15

export function localConverter(origin) {
  const lat0 = Number(origin[0])
  const lng0 = Number(origin[1])
  const kx = M_PER_DEG_LNG * Math.cos((lat0 * Math.PI) / 180)
  return {
    toLocal: ([lat, lng]) => [(lng - lng0) * kx, (lat - lat0) * M_PER_DEG_LAT],
    toLatLng: ([x, y]) => [lat0 + y / M_PER_DEG_LAT, lng0 + x / kx],
  }
}

export function idaeRowGap(panelLengthM, betaDeg, latDeg) {
  const beta = (Math.abs(betaDeg || 0) * Math.PI) / 180
  const solarLimit = 61 - Math.min(Math.abs(latDeg || 40), 60)
  const h = panelLengthM * Math.sin(beta)
  return h / Math.tan((solarLimit * Math.PI) / 180)
}

export function sunVector(latDeg, declDeg, hourAngleDeg) {
  const phi = (latDeg * Math.PI) / 180
  const dec = (declDeg * Math.PI) / 180
  const omega = (hourAngleDeg * Math.PI) / 180
  return [
    -Math.cos(dec) * Math.sin(omega),
    Math.cos(phi) * Math.sin(dec) - Math.sin(phi) * Math.cos(dec) * Math.cos(omega),
    Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(omega),
  ]
}

export function makeGrid({ origin, azimut, rotation, phase, orientation, panelWmm, panelHmm, beta, coplanar, lat, rowGap, colGap }) {
  const conv = localConverter(origin)
  const wM = (orientation === 'h' ? panelHmm : panelWmm) / 1000
  const lengthM = (orientation === 'h' ? panelWmm : panelHmm) / 1000
  const betaDeg = beta || 0
  const depthM = lengthM * Math.cos((betaDeg * Math.PI) / 180)
  const gapRow = rowGap != null ? rowGap : (coplanar ? DEFAULT_GAP : Math.max(DEFAULT_GAP, idaeRowGap(lengthM, betaDeg, lat)))
  const gapCol = colGap != null ? colGap : DEFAULT_GAP
  const pitchX = wM + gapCol
  const pitchY = depthM + gapRow
  const [phaseU, phaseV] = phase || [0, 0]

  const phi = (((rotation ?? azimut ?? 180) * Math.PI) / 180)
  const d = [Math.sin(phi), Math.cos(phi)]
  const r = [-d[1], d[0]]

  function cellCenterLocal(i, j) {
    const u = i * pitchX + phaseU
    const v = j * pitchY + phaseV
    return [u * r[0] + v * d[0], u * r[1] + v * d[1]]
  }

  function cellCornersLocal(i, j) {
    const [cx, cy] = cellCenterLocal(i, j)
    const hw = wM / 2
    const hd = depthM / 2
    return [
      [cx - hw * r[0] - hd * d[0], cy - hw * r[1] - hd * d[1]],
      [cx + hw * r[0] - hd * d[0], cy + hw * r[1] - hd * d[1]],
      [cx + hw * r[0] + hd * d[0], cy + hw * r[1] + hd * d[1]],
      [cx - hw * r[0] + hd * d[0], cy - hw * r[1] + hd * d[1]],
    ]
  }

  function pointToCellFloat([x, y]) {
    return [((x * r[0] + y * r[1]) - phaseU) / pitchX, ((x * d[0] + y * d[1]) - phaseV) / pitchY]
  }

  return {
    conv,
    wM,
    depthM,
    pitchX,
    pitchY,
    gapRow,
    rotation: rotation ?? azimut ?? 180,
    cellCenterLocal,
    cellCornersLocal,
    cellPolygon: (i, j) => cellCornersLocal(i, j).map(conv.toLatLng),
    latLngToCell: (latlng) => {
      const [u, v] = pointToCellFloat(conv.toLocal(latlng))
      return [Math.round(u), Math.round(v)]
    },
    pointToCellFloat,
  }
}

export function pointInPolygon([x, y], poly) {
  let inside = false
  for (let a = 0, b = poly.length - 1; a < poly.length; b = a++) {
    const [xa, ya] = poly[a]
    const [xb, yb] = poly[b]
    const intersects = (ya > y) !== (yb > y) && x < ((xb - xa) * (y - ya)) / (yb - ya) + xa
    if (intersects) inside = !inside
  }
  return inside
}

export function distanceToPolygonEdge([x, y], poly) {
  let best = Infinity
  for (let a = 0, b = poly.length - 1; a < poly.length; b = a++) {
    const [xa, ya] = poly[a]
    const [xb, yb] = poly[b]
    const dx = xb - xa
    const dy = yb - ya
    const lenSq = dx * dx + dy * dy || 1e-12
    const t = Math.max(0, Math.min(1, ((x - xa) * dx + (y - ya) * dy) / lenSq))
    const px = xa + t * dx
    const py = ya + t * dy
    const dist = Math.hypot(x - px, y - py)
    if (dist < best) best = dist
  }
  return best
}

export function cellFits(grid, i, j, roofLocal, exclusionsLocal, opts) {
  const corners = grid.cellCornersLocal(i, j)
  const [cx, cy] = grid.cellCenterLocal(i, j)
  const points = [...corners, [cx, cy]]
  const setback = opts?.setbackM || 0
  const anchorable = opts?.anchorableLocal
  for (const p of points) {
    if (!pointInPolygon(p, roofLocal)) return false
    if (anchorable && anchorable.length >= 3 && !pointInPolygon(p, anchorable)) return false
    for (const exc of exclusionsLocal) {
      if (pointInPolygon(p, exc.poly || exc)) return false
    }
  }
  if (setback > 0) {
    for (const p of corners) {
      if (distanceToPolygonEdge(p, roofLocal) < setback) return false
    }
  }
  return true
}

export function cellKey(i, j) {
  return `${i},${j}`
}

export function parseKey(key) {
  const [i, j] = key.split(',').map(Number)
  return [i, j]
}

function cellRange(grid, roofLocal) {
  let minU = Infinity
  let maxU = -Infinity
  let minV = Infinity
  let maxV = -Infinity
  for (const p of roofLocal) {
    const [u, v] = grid.pointToCellFloat(p)
    minU = Math.min(minU, u)
    maxU = Math.max(maxU, u)
    minV = Math.min(minV, v)
    maxV = Math.max(maxV, v)
  }
  return [Math.floor(minU) - 1, Math.ceil(maxU) + 1, Math.floor(minV) - 1, Math.ceil(maxV) + 1]
}

export function autoLayoutCells(grid, roofLocal, exclusionsLocal, opts) {
  const cells = []
  if (roofLocal.length < 3) return cells
  const [i0, i1, j0, j1] = cellRange(grid, roofLocal)
  for (let j = j0; j <= j1; j++) {
    for (let i = i0; i <= i1; i++) {
      if (cellFits(grid, i, j, roofLocal, exclusionsLocal, opts)) cells.push([i, j])
    }
  }
  return cells
}

export function fillBetweenCells(grid, anchor, target, roofLocal, exclusionsLocal, occupied) {
  const cells = []
  const i0 = Math.min(anchor[0], target[0])
  const i1 = Math.max(anchor[0], target[0])
  const j0 = Math.min(anchor[1], target[1])
  const j1 = Math.max(anchor[1], target[1])
  for (let j = j0; j <= j1; j++) {
    for (let i = i0; i <= i1; i++) {
      const key = cellKey(i, j)
      if (occupied.has(key)) continue
      if (cellFits(grid, i, j, roofLocal, exclusionsLocal)) cells.push([i, j])
    }
  }
  return cells
}

export function shadingWindow(latDeg) {
  const samples = []
  const half = (SHADING_WINDOW_HOURS / 2) * 15
  for (let omega = -half; omega <= half + 1e-9; omega += (SHADING_STEP_MIN / 60) * 15) {
    const sun = sunVector(latDeg, WINTER_DECLINATION, omega)
    if (sun[2] > 0.02) samples.push(sun)
  }
  return samples
}

export function obstacleShadingScores(grid, fitCells, obstaclesLocal, latDeg, planeElevationM = 0) {
  const scores = new Map()
  if (!obstaclesLocal?.length || !fitCells.length) return scores
  const samples = shadingWindow(latDeg)
  if (!samples.length) return scores

  const casters = obstaclesLocal
    .map((o) => ({
      poly: o.poly,
      opacity: 1 - Math.max(0, Math.min(1, o.transmittance ?? 0)),
      h: (o.baseElevationM ?? planeElevationM) + (o.heightM || 0) - planeElevationM,
    }))
    .filter((o) => o.h > 0.05 && o.opacity > 0 && o.poly?.length >= 3)
  if (!casters.length) return scores

  const shadowPolys = casters.map((o) =>
    samples.map((sun) => {
      const fx = -sun[0] / sun[2] * o.h
      const fy = -sun[1] / sun[2] * o.h
      const swept = []
      for (const [x, y] of o.poly) {
        swept.push([x, y])
        swept.push([x + fx, y + fy])
      }
      return { hull: convexHull(swept), opacity: o.opacity }
    })
  )

  for (const [i, j] of fitCells) {
    const c = grid.cellCenterLocal(i, j)
    let shaded = 0
    for (let t = 0; t < samples.length; t++) {
      let opacity = 0
      for (const perObstacle of shadowPolys) {
        const s = perObstacle[t]
        if (pointInPolygon(c, s.hull)) opacity = Math.max(opacity, s.opacity)
      }
      shaded += opacity
    }
    const score = shaded / samples.length
    if (score > 0) scores.set(cellKey(i, j), score)
  }
  return scores
}

export function convexHull(points) {
  const pts = [...new Map(points.map((p) => [`${p[0].toFixed(4)},${p[1].toFixed(4)}`, p])).values()]
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
  if (pts.length <= 2) return pts
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const lower = []
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop()
    lower.push(p)
  }
  const upper = []
  for (const p of [...pts].reverse()) {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop()
    upper.push(p)
  }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)]
}

export function selectBest(fitCells, required, shadeScores) {
  if (!required || fitCells.length <= required) return [...fitCells]
  const rows = new Map()
  for (const [i, j] of fitCells) {
    if (!rows.has(j)) rows.set(j, [])
    rows.get(j).push(i)
  }
  const rowStats = [...rows.entries()].map(([j, is]) => {
    const shade = is.reduce((s, i) => s + (shadeScores?.get(cellKey(i, j)) || 0), 0) / is.length
    return { j, is: is.sort((a, b) => a - b), shade }
  })
  const medianJ = rowStats.map((r) => r.j).sort((a, b) => a - b)[Math.floor(rowStats.length / 2)]
  rowStats.sort((a, b) => (a.shade - b.shade) || (Math.abs(a.j - medianJ) - Math.abs(b.j - medianJ)))

  const picked = []
  for (const row of rowStats) {
    const remaining = required - picked.length
    if (remaining <= 0) break
    if (row.is.length <= remaining) {
      picked.push(...row.is.map((i) => [i, row.j]))
    } else {
      const scored = row.is.map((i) => ({ i, s: shadeScores?.get(cellKey(i, row.j)) || 0 }))
      let best = { start: 0, sum: Infinity }
      for (let start = 0; start + remaining <= scored.length; start++) {
        let sum = 0
        let contiguous = true
        for (let k = 0; k < remaining; k++) {
          sum += scored[start + k].s
          if (k > 0 && scored[start + k].i !== scored[start + k - 1].i + 1) contiguous = false
        }
        if (contiguous) sum -= 0.001
        if (sum < best.sum) best = { start, sum }
      }
      for (let k = 0; k < remaining; k++) picked.push([scored[best.start + k].i, row.j])
    }
  }
  return picked
}

export function assignStrings(cells, stringCount) {
  const n = Math.max(1, Math.floor(stringCount) || 1)
  const ordered = [...cells].sort((a, b) => (a[1] - b[1]) || (a[0] - b[0]))
  const base = Math.floor(ordered.length / n)
  const extra = ordered.length % n
  const groups = []
  let cursor = 0
  for (let k = 0; k < n; k++) {
    const size = base + (k < extra ? 1 : 0)
    groups.push(ordered.slice(cursor, cursor + size).map(([i, j]) => cellKey(i, j)))
    cursor += size
  }
  return groups
}

export function orientationLossPct(rowRotationDeg, moduleAzimutDeg) {
  const delta = ((rowRotationDeg - moduleAzimutDeg + 540) % 360) - 180
  return 3.5 * 0.00001 * delta * delta * 100
}

export function optimizeLayout({
  origin, moduleAzimut, coplanar, orientationChoices, panelWmm, panelHmm, beta, lat,
  rowGap, colGap, roofLocal, exclusionsLocal, obstaclesLocal, required,
  setbackM, anchorableLocal, structuralAzimut, planeElevationM,
}) {
  if (!roofLocal || roofLocal.length < 3) return null
  const orientations = orientationChoices || ['v', 'h']
  const fitOpts = { setbackM, anchorableLocal }
  const req = Number(required) || 0

  function evaluate(rotation, orientation, phase) {
    const grid = makeGrid({
      origin, rotation, phase, orientation, panelWmm, panelHmm,
      beta, coplanar, lat, rowGap, colGap,
    })
    const fit = autoLayoutCells(grid, roofLocal, exclusionsLocal, fitOpts)
    if (!fit.length) return null
    const shadeScores = obstacleShadingScores(grid, fit, obstaclesLocal, lat, planeElevationM)
    const chosen = req > 0 ? selectBest(fit, req, shadeScores) : fit
    const shadeTotal = chosen.reduce((s, [i, j]) => s + (shadeScores.get(cellKey(i, j)) || 0), 0)
    const lossPct = coplanar ? 0 : orientationLossPct(rotation, moduleAzimut ?? 180)
    let structuralPenalty = 0
    if (structuralAzimut != null) {
      const misalign = Math.min(
        ...[0, 90, 180, 270].map((k) => {
          const d = Math.abs(((rotation - structuralAzimut - k + 540) % 360) - 180)
          return d
        })
      )
      structuralPenalty = misalign > 5 ? misalign : 0
    }
    const satisfied = req > 0 ? Math.min(fit.length, req) : fit.length
    const score = satisfied * 1000
      - shadeTotal * 400
      - lossPct * satisfied * 2
      - structuralPenalty * 5
      + (req > 0 && fit.length >= req ? 500 : 0)
    return { rotation, orientation, phase, grid, fit, cells: chosen, shadeScores, score, lossPct }
  }

  let best = null
  const consider = (cand) => {
    if (cand && (!best || cand.score > best.score)) best = cand
  }

  for (const orientation of orientations) {
    const probe = makeGrid({
      origin, rotation: 0, orientation, panelWmm, panelHmm, beta, coplanar, lat, rowGap, colGap,
    })
    const coarsePhases = []
    for (let a = 0; a < 3; a++) {
      for (let b = 0; b < 3; b++) {
        coarsePhases.push([(a / 3) * probe.pitchX, (b / 3) * probe.pitchY])
      }
    }
    for (let rot = 0; rot < 180; rot += 15) {
      for (const phase of coarsePhases) consider(evaluate(rot, orientation, phase))
    }
  }
  if (!best) return null

  const centerRot = best.rotation
  const orientation = best.orientation
  const refine = makeGrid({
    origin, rotation: centerRot, orientation, panelWmm, panelHmm, beta, coplanar, lat, rowGap, colGap,
  })
  for (let rot = centerRot - 10; rot <= centerRot + 10; rot += 5) {
    const r = ((rot % 180) + 180) % 180
    for (let a = 0; a < 6; a++) {
      for (let b = 0; b < 6; b++) {
        consider(evaluate(r, orientation, [(a / 6) * refine.pitchX, (b / 6) * refine.pitchY]))
      }
    }
  }
  return best
}

export function polygonAreaM2(polyLocal) {
  let sum = 0
  for (let a = 0, b = polyLocal.length - 1; a < polyLocal.length; b = a++) {
    sum += (polyLocal[b][0] + polyLocal[a][0]) * (polyLocal[b][1] - polyLocal[a][1])
  }
  return Math.abs(sum / 2)
}

export function centroid(points) {
  let lat = 0
  let lng = 0
  for (const p of points) {
    lat += Number(p[0])
    lng += Number(p[1])
  }
  return [lat / points.length, lng / points.length]
}

export function bearingBetween(convOrOrigin, aLatLng, bLatLng) {
  const conv = typeof convOrOrigin.toLocal === 'function' ? convOrOrigin : localConverter(convOrOrigin)
  const [ax, ay] = conv.toLocal(aLatLng)
  const [bx, by] = conv.toLocal(bLatLng)
  return ((Math.atan2(bx - ax, by - ay) * 180) / Math.PI + 360) % 360
}

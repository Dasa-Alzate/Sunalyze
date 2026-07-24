const M_PER_DEG_LAT = 110574
const M_PER_DEG_LNG = 111320

const DEFAULT_GAP = 0.02

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

export function makeGrid({ origin, azimut, orientation, panelWmm, panelHmm, beta, coplanar, lat, rowGap, colGap }) {
  const conv = localConverter(origin)
  const wM = (orientation === 'h' ? panelHmm : panelWmm) / 1000
  const lengthM = (orientation === 'h' ? panelWmm : panelHmm) / 1000
  const betaDeg = beta || 0
  const depthM = lengthM * Math.cos((betaDeg * Math.PI) / 180)
  const gapRow = rowGap != null ? rowGap : (coplanar ? DEFAULT_GAP : Math.max(DEFAULT_GAP, idaeRowGap(lengthM, betaDeg, lat)))
  const gapCol = colGap != null ? colGap : DEFAULT_GAP
  const pitchX = wM + gapCol
  const pitchY = depthM + gapRow

  const phi = (((azimut ?? 180) * Math.PI) / 180)
  const d = [Math.sin(phi), Math.cos(phi)]
  const r = [-d[1], d[0]]

  function cellCenterLocal(i, j) {
    return [i * pitchX * r[0] + j * pitchY * d[0], i * pitchX * r[1] + j * pitchY * d[1]]
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
    return [(x * r[0] + y * r[1]) / pitchX, (x * d[0] + y * d[1]) / pitchY]
  }

  return {
    conv,
    wM,
    depthM,
    pitchX,
    pitchY,
    gapRow,
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

export function cellFits(grid, i, j, roofLocal, exclusionsLocal) {
  const corners = grid.cellCornersLocal(i, j)
  const [cx, cy] = grid.cellCenterLocal(i, j)
  const points = [...corners, [cx, cy]]
  for (const p of points) {
    if (!pointInPolygon(p, roofLocal)) return false
    for (const exc of exclusionsLocal) {
      if (pointInPolygon(p, exc)) return false
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

export function autoLayoutCells(grid, roofLocal, exclusionsLocal) {
  const cells = []
  if (roofLocal.length < 3) return cells
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
  for (let j = Math.floor(minV) - 1; j <= Math.ceil(maxV) + 1; j++) {
    for (let i = Math.floor(minU) - 1; i <= Math.ceil(maxU) + 1; i++) {
      if (cellFits(grid, i, j, roofLocal, exclusionsLocal)) cells.push([i, j])
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

import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Btn, Icon } from '@/shared/ui'
import { toast } from '@/services/toast'
import {
  makeGrid, localConverter, cellFits, cellKey, parseKey,
  autoLayoutCells, fillBetweenCells, polygonAreaM2, centroid,
  optimizeLayout, obstacleShadingScores, bearingBetween, sunVector, convexHull,
  assignStrings, annualShadeFactors, orientationLossPct,
} from './layoutEngine'
import './panel-layout.css'

const PNOA_URL = 'https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile&version=1.0.0'
  + '&layer=OI.OrthoimageCoverage&style=default&format=image/jpeg'
  + '&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}'
const CATASTRO_URL = 'https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx'

const STYLE_ROOF = { color: '#38bdf8', weight: 2, dashArray: '6 4', fillColor: '#38bdf8', fillOpacity: 0.06 }
const STYLE_EXCLUSION = { color: '#ef4444', weight: 1.5, dashArray: '4 3', fillColor: '#ef4444', fillOpacity: 0.18 }
const STYLE_OBSTACLE = { color: '#d9920a', weight: 1.5, fillColor: '#d9920a', fillOpacity: 0.3 }
const STYLE_SHADOW = { color: '#334155', weight: 0, fillColor: '#334155', fillOpacity: 0.18, interactive: false }
const STYLE_MEASURE = { color: '#8b5cf6', weight: 2.5, dashArray: '8 5' }
const STYLE_PANEL = { color: '#e2e8f0', weight: 1, fillColor: '#0f2c52', fillOpacity: 0.85 }
const STYLE_PANEL_SELECTED = { color: '#f59e0b', weight: 2, fillColor: '#1d4ed8', fillOpacity: 0.9 }
const STYLE_DRAFT = { color: '#38bdf8', weight: 2, dashArray: '4 4' }

const VERTEX_ICON = L.divIcon({ className: 'pl-vertex', iconSize: [11, 11], iconAnchor: [5.5, 5.5] })

const STRING_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']

const HEAT_RAMP = ['#fde3cf', '#f5a15f', '#eb6834', '#b8420f', '#7a2e05']

function heatColor(t) {
  const pos = Math.max(0, Math.min(1, t)) * (HEAT_RAMP.length - 1)
  const lo = Math.floor(pos)
  const hi = Math.min(HEAT_RAMP.length - 1, lo + 1)
  const f = pos - lo
  const a = HEAT_RAMP[lo]
  const b = HEAT_RAMP[hi]
  const mix = (i) => Math.round(
    parseInt(a.slice(i, i + 2), 16) * (1 - f) + parseInt(b.slice(i, i + 2), 16) * f
  )
  return `rgb(${mix(1)}, ${mix(3)}, ${mix(5)})`
}

function isTyping(e) {
  const el = e.target
  return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable)
}

export default function PanelLayout({ lat, lon, azimut, inclinacion, coplanar, betaOptimal, panel, requiredPanels, stringConfig, poaAnnual, layout, onChange }) {
  const [roof, setRoof] = useState(() => layout?.roof || [])
  const [exclusions, setExclusions] = useState(() => layout?.exclusions || [])
  const [cells, setCells] = useState(() => (layout?.cells || []).map(([i, j]) => [i, j]))
  const [orientation, setOrientation] = useState(() => layout?.orientation || 'v')
  const [rowGapOverride, setRowGapOverride] = useState(() => layout?.row_gap_m ?? null)
  const [rotation, setRotation] = useState(() => layout?.rotation ?? null)
  const [phase, setPhase] = useState(() => layout?.phase || null)
  const [obstacles, setObstacles] = useState(() => layout?.obstacles || [])
  const [obstacleHeight, setObstacleHeight] = useState('2')
  const [origin, setOrigin] = useState(() => layout?.origin || null)
  const [selection, setSelection] = useState(() => new Set())
  const [mode, setMode] = useState('idle')
  const [showCatastro, setShowCatastro] = useState(false)
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [gapDraft, setGapDraft] = useState(() => (layout?.row_gap_m != null ? String(layout.row_gap_m) : ''))

  const mapEl = useRef(null)
  const mapRef = useRef(null)
  const catastroRef = useRef(null)
  const heatLayerRef = useRef(null)
  const roofLayerRef = useRef(null)
  const vertexLayerRef = useRef(null)
  const exclusionLayerRef = useRef(null)
  const obstacleLayerRef = useRef(null)
  const panelLayerRef = useRef(null)
  const panelIndexRef = useRef(new Map())
  const draftLayerRef = useRef(null)
  const draftRef = useRef([])
  const mouseLatLngRef = useRef(null)
  const clipboardRef = useRef(null)
  const dragRef = useRef(null)
  const justDraggedRef = useRef(false)
  const stateRef = useRef({})
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange
  const readyRef = useRef(false)

  const beta = coplanar ? Number(inclinacion) || 0 : Number(betaOptimal) || 0
  const gridAzimut = coplanar ? (Number(azimut) || 180) : 180

  const grid = useMemo(() => {
    if (!origin || !panel?.width || !panel?.height) return null
    return makeGrid({
      origin,
      azimut: gridAzimut,
      rotation: rotation ?? undefined,
      phase: phase ?? undefined,
      orientation,
      panelWmm: panel.width,
      panelHmm: panel.height,
      beta,
      coplanar: !!coplanar,
      lat: Number(lat) || 40,
      rowGap: rowGapOverride,
      colGap: null,
    })
  }, [origin, gridAzimut, rotation, phase, orientation, panel?.width, panel?.height, beta, coplanar, lat, rowGapOverride])

  const geo = useMemo(() => {
    if (!origin) return null
    const conv = localConverter(origin)
    return {
      conv,
      roofLocal: roof.map(conv.toLocal),
      exclusionsLocal: exclusions.map((poly) => poly.map(conv.toLocal)),
      obstaclesLocal: obstacles.map((o) => ({
        poly: o.poly.map(conv.toLocal),
        heightM: o.height_m,
        baseElevationM: o.base_elevation_m ?? null,
        transmittance: o.transmittance ?? 0,
      })),
    }
  }, [origin, roof, exclusions, obstacles])

  const stringGroups = useMemo(() => {
    const n = Number(stringConfig?.n_parallel) || 0
    if (!n || n < 2 || !cells.length) return null
    return assignStrings(cells, n)
  }, [cells, stringConfig?.n_parallel])

  const stringIndex = useMemo(() => {
    if (!stringGroups) return null
    const map = new Map()
    stringGroups.forEach((keys, idx) => keys.forEach((k) => map.set(k, idx)))
    return map
  }, [stringGroups])

  const layoutSummary = useMemo(() => {
    if (!grid || !geo || geo.roofLocal.length < 3 || !cells.length) return null
    const factors = annualShadeFactors(grid, cells, geo.obstaclesLocal, Number(lat) || 40)
    const shade = cells.reduce((s, [i, j]) => s + (factors.get(cellKey(i, j)) || 0), 0) / cells.length
    const orientation = coplanar || rotation == null ? 0 : orientationLossPct(rotation, gridAzimut)
    return {
      placed_panels: cells.length,
      shade_loss_pct: Math.round(shade * 1000) / 10,
      orientation_loss_pct: Math.round(orientation * 10) / 10,
    }
  }, [grid, geo, cells, lat, coplanar, rotation, gridAzimut])

  const heatData = useMemo(() => {
    if (!showHeatmap || !grid || !geo || geo.roofLocal.length < 3) return null
    const fit = autoLayoutCells(grid, geo.roofLocal, geo.exclusionsLocal)
    if (!fit.length) return null
    const factors = annualShadeFactors(grid, fit, geo.obstaclesLocal, Number(lat) || 40)
    const poa = Number(poaAnnual) || null
    let min = Infinity
    let max = -Infinity
    const values = fit.map(([i, j]) => {
      const f = factors.get(cellKey(i, j)) || 0
      const v = poa ? poa * (1 - f) : (1 - f) * 100
      if (v < min) min = v
      if (v > max) max = v
      return { i, j, v }
    })
    return { values, min, max, unit: poa ? 'kWh/m²·año' : '% de sol anual' }
  }, [showHeatmap, grid, geo, lat, poaAnnual])

  stateRef.current = { roof, exclusions, obstacles, obstacleHeight, cells, selection, mode, grid, geo, origin }

  useEffect(() => {
    if (!readyRef.current) { readyRef.current = true; return }
    if (!onChangeRef.current) return
    if (!roof.length && !cells.length) { onChangeRef.current(null); return }
    onChangeRef.current({
      roof,
      exclusions,
      obstacles,
      cells,
      orientation,
      rotation,
      phase,
      origin,
      azimut: gridAzimut,
      beta,
      coplanar: !!coplanar,
      row_gap_m: rowGapOverride,
      col_gap_m: null,
      panel: panel ? { w_mm: panel.width, h_mm: panel.height } : null,
      strings: stringGroups,
      summary: layoutSummary,
    })
  }, [roof, exclusions, obstacles, cells, orientation, rotation, phase, origin, rowGapOverride, stringGroups, layoutSummary])

  function commitCells(next, nextSelection) {
    setCells(next)
    if (nextSelection) setSelection(nextSelection)
  }

  function pruneCells(nextGridDeps) {
    const { grid: g, geo: gg } = nextGridDeps || stateRef.current
    if (!g || !gg || gg.roofLocal.length < 3) return
    setCells((prev) => {
      const kept = prev.filter(([i, j]) => cellFits(g, i, j, gg.roofLocal, gg.exclusionsLocal))
      if (kept.length !== prev.length) {
        toast('info', 'Disposición ajustada', `${prev.length - kept.length} panel(es) ya no cabían y se retiraron`)
        setSelection(new Set())
      }
      return kept.length !== prev.length ? kept : prev
    })
  }

  useEffect(() => {
    if (grid && geo && geo.roofLocal.length >= 3) pruneCells({ grid, geo })
  }, [grid, geo])

  function finishDraft() {
    const draft = draftRef.current
    const { mode: m } = stateRef.current
    if (draft.length >= 3) {
      if (m === 'draw-roof') {
        setRoof(draft.map((p) => [p[0], p[1]]))
        if (!stateRef.current.origin) setOrigin(centroid(draft))
        setCells([])
        setSelection(new Set())
      } else if (m === 'draw-exclusion') {
        setExclusions((list) => [...list, draft.map((p) => [p[0], p[1]])])
      } else if (m === 'draw-obstacle') {
        const h = Math.max(0.1, Number(stateRef.current.obstacleHeight) || 2)
        setObstacles((list) => [...list, { poly: draft.map((p) => [p[0], p[1]]), height_m: h }])
        toast('info', `Obstáculo de ${h} m añadido`, 'Su sombra de invierno se muestra en gris y penaliza la colocación automática')
      }
    }
    draftRef.current = []
    draftLayerRef.current?.clearLayers()
    setMode('idle')
  }

  function handleMeasureClick(latlng) {
    const pts = draftRef.current
    pts.push([latlng.lat, latlng.lng])
    if (pts.length < 3) {
      redrawDraft()
      return
    }
    const [a, b, c] = pts
    const conv = localConverter(a)
    const [bx, by] = conv.toLocal(b)
    const [cx, cy] = conv.toLocal(c)
    const lineBearing = bearingBetween(conv, a, b)
    const side = bx * cy - by * cx
    const rot = (Math.round((((lineBearing + (side < 0 ? 90 : -90)) % 360 + 360) % 360) / 5) * 5) % 360
    setRotation(rot)
    draftRef.current = []
    draftLayerRef.current?.clearLayers()
    setMode('idle')
    toast('success', `Filas orientadas a ${rot % 360}°`, `Paralelas a la línea medida (${Math.round(lineBearing)}°), mirando hacia el lado marcado`)
  }

  function cancelDraft() {
    draftRef.current = []
    draftLayerRef.current?.clearLayers()
    setMode('idle')
  }

  function redrawDraft(cursor) {
    const layer = draftLayerRef.current
    if (!layer) return
    layer.clearLayers()
    const draft = draftRef.current
    if (!draft.length) return
    const m = stateRef.current.mode
    const style = m === 'draw-exclusion' ? STYLE_EXCLUSION
      : m === 'draw-obstacle' ? STYLE_OBSTACLE
      : m === 'measure-azimut' ? STYLE_MEASURE
      : STYLE_DRAFT
    const pts = cursor ? [...draft, cursor] : draft
    L.polyline(pts, style).addTo(layer)
    draft.forEach((p, idx) => {
      L.marker(p, { icon: VERTEX_ICON, interactive: idx === 0, keyboard: false })
        .on('click', () => { if (draftRef.current.length >= 3) finishDraft() })
        .addTo(layer)
    })
  }

  function selectAll() {
    const { cells: cs } = stateRef.current
    setSelection(new Set(cs.map(([i, j]) => cellKey(i, j))))
  }

  function copySelection() {
    const { selection: sel } = stateRef.current
    if (!sel.size) return
    const parsed = [...sel].map(parseKey)
    const minI = Math.min(...parsed.map(([i]) => i))
    const minJ = Math.min(...parsed.map(([, j]) => j))
    clipboardRef.current = parsed.map(([i, j]) => [i - minI, j - minJ])
    toast('info', `${sel.size} panel(es) copiados`, 'Pega con ⌘V / Ctrl+V sobre el tejado')
  }

  function pasteClipboard() {
    const clip = clipboardRef.current
    const { grid: g, geo: gg, cells: cs } = stateRef.current
    if (!clip || !clip.length || !g || !gg) return
    const at = mouseLatLngRef.current
    let base
    if (at) {
      base = g.latLngToCell([at.lat, at.lng])
    } else {
      const parsed = cs.length ? cs : [[0, 0]]
      base = [Math.max(...parsed.map(([i]) => i)) + 2, Math.min(...parsed.map(([, j]) => j))]
    }
    const spanI = Math.max(...clip.map(([i]) => i))
    const spanJ = Math.max(...clip.map(([, j]) => j))
    const start = [base[0] - Math.round(spanI / 2), base[1] - Math.round(spanJ / 2)]
    const occupied = new Set(cs.map(([i, j]) => cellKey(i, j)))
    const placed = []
    for (const [di, dj] of clip) {
      const i = start[0] + di
      const j = start[1] + dj
      const key = cellKey(i, j)
      if (occupied.has(key)) continue
      if (!cellFits(g, i, j, gg.roofLocal, gg.exclusionsLocal)) continue
      occupied.add(key)
      placed.push([i, j])
    }
    if (!placed.length) {
      toast('warning', 'No hay sitio libre ahí', 'Apunta con el ratón a una zona libre de la cubierta y vuelve a pegar')
      return
    }
    commitCells([...cs, ...placed], new Set(placed.map(([i, j]) => cellKey(i, j))))
  }

  function deleteSelection() {
    const { selection: sel, cells: cs } = stateRef.current
    if (!sel.size) return
    commitCells(cs.filter(([i, j]) => !sel.has(cellKey(i, j))), new Set())
  }

  function autoLayout() {
    const { geo: gg, origin: org } = stateRef.current
    if (!org || !gg || gg.roofLocal.length < 3 || !panel?.width || !panel?.height) return
    const req = Number(requiredPanels) || 0
    const best = optimizeLayout({
      origin: org,
      moduleAzimut: gridAzimut,
      coplanar: !!coplanar,
      panelWmm: panel.width,
      panelHmm: panel.height,
      beta,
      lat: Number(lat) || 40,
      rowGap: rowGapOverride,
      colGap: null,
      roofLocal: gg.roofLocal,
      exclusionsLocal: gg.exclusionsLocal,
      obstaclesLocal: gg.obstaclesLocal,
      required: req,
    })
    if (!best) {
      toast('warning', 'No cabe ningún panel', 'Revisa la cubierta y las exclusiones')
      return
    }
    setRotation(best.rotation)
    setPhase(best.phase)
    if (best.orientation !== orientation) setOrientation(best.orientation)
    commitCells(best.cells, new Set())

    const shaded = best.cells.filter(([i, j]) => (best.shadeScores.get(cellKey(i, j)) || 0) > 0.25).length
    const bits = [`retícula a ${Math.round(best.rotation)}°`]
    if (!coplanar && best.lossPct > 0.05) bits.push(`coste de orientación ${best.lossPct.toFixed(1)}%`)
    if (shaded) bits.push(`${shaded} con sombra parcial de obstáculos`)
    if (req > 0 && best.fit.length > req) {
      toast('success', `${best.cells.length} paneles colocados`, `Caben ${best.fit.length}; ${bits.join(' · ')}`)
    } else if (req > 0 && best.cells.length < req) {
      toast('warning', `Solo caben ${best.cells.length} de ${req}`, 'Amplía la cubierta, aprieta las filas o cambia de panel')
    } else {
      toast('success', `${best.cells.length} paneles colocados`, bits.join(' · '))
    }
  }

  function fillTo(targetLatLng) {
    const { grid: g, geo: gg, selection: sel, cells: cs } = stateRef.current
    if (!g || !gg || !sel.size) return
    const anchorKey = [...sel][sel.size - 1]
    const anchor = parseKey(anchorKey)
    const target = g.latLngToCell(targetLatLng)
    const occupied = new Set(cs.map(([i, j]) => cellKey(i, j)))
    const added = fillBetweenCells(g, anchor, target, gg.roofLocal, gg.exclusionsLocal, occupied)
    if (!added.length) return
    commitCells([...cs, ...added], new Set([...sel, ...added.map(([i, j]) => cellKey(i, j))]))
  }

  function onPanelClick(key, ev) {
    if (justDraggedRef.current) {
      justDraggedRef.current = false
      return
    }
    if (stateRef.current.mode !== 'idle') {
      draftRef.current = [...draftRef.current, [ev.latlng.lat, ev.latlng.lng]]
      redrawDraft()
      return
    }
    const shift = ev.originalEvent.shiftKey
    setSelection((prev) => {
      if (shift) {
        const next = new Set(prev)
        if (next.has(key)) next.delete(key)
        else next.add(key)
        return next
      }
      return new Set([key])
    })
  }

  function beginPanelDrag(key, ev) {
    const { selection: sel } = stateRef.current
    if (!sel.has(key) || stateRef.current.mode !== 'idle') return
    const map = mapRef.current
    ev.originalEvent.preventDefault()
    map.dragging.disable()
    dragRef.current = { startLatLng: ev.latlng, delta: [0, 0] }
  }

  useEffect(() => {
    if (!mapEl.current || mapRef.current) return undefined
    const start = [Number(lat) || 40.4168, Number(lon) || -3.7038]
    const map = L.map(mapEl.current, { center: start, zoom: 20, maxZoom: 22, doubleClickZoom: false })
    L.tileLayer(PNOA_URL, {
      attribution: '&copy; <a href="https://www.ign.es">Instituto Geográfico Nacional de España (PNOA)</a>',
      maxNativeZoom: 20,
      maxZoom: 22,
    }).addTo(map)
    catastroRef.current = L.tileLayer.wms(CATASTRO_URL, {
      layers: 'Catastro', format: 'image/png', transparent: true, version: '1.1.1',
      attribution: '&copy; D.G. Catastro',
    })
    heatLayerRef.current = L.layerGroup().addTo(map)
    roofLayerRef.current = L.layerGroup().addTo(map)
    vertexLayerRef.current = L.layerGroup().addTo(map)
    exclusionLayerRef.current = L.layerGroup().addTo(map)
    obstacleLayerRef.current = L.layerGroup().addTo(map)
    panelLayerRef.current = L.layerGroup().addTo(map)
    draftLayerRef.current = L.layerGroup().addTo(map)

    map.on('click', (e) => {
      const { mode: m, selection: sel } = stateRef.current
      if (m === 'measure-azimut') {
        handleMeasureClick(e.latlng)
        return
      }
      if (m === 'draw-roof' || m === 'draw-exclusion' || m === 'draw-obstacle') {
        const first = draftRef.current[0]
        if (first && draftRef.current.length >= 3) {
          const d = map.latLngToContainerPoint(e.latlng).distanceTo(map.latLngToContainerPoint(first))
          if (d < 12) { finishDraft(); return }
        }
        draftRef.current = [...draftRef.current, [e.latlng.lat, e.latlng.lng]]
        redrawDraft()
        return
      }
      if (e.originalEvent.shiftKey && sel.size) {
        fillTo([e.latlng.lat, e.latlng.lng])
        return
      }
      setSelection(new Set())
    })

    map.on('dblclick', () => {
      const { mode: m } = stateRef.current
      if (m === 'draw-roof' || m === 'draw-exclusion' || m === 'draw-obstacle') finishDraft()
    })

    map.on('mousemove', (e) => {
      mouseLatLngRef.current = e.latlng
      const { mode: m, grid: g } = stateRef.current
      if (m === 'draw-roof' || m === 'draw-exclusion' || m === 'draw-obstacle' || m === 'measure-azimut') {
        if (draftRef.current.length) redrawDraft([e.latlng.lat, e.latlng.lng])
        return
      }
      const drag = dragRef.current
      if (drag && g) {
        const from = g.pointToCellFloat(g.conv.toLocal([drag.startLatLng.lat, drag.startLatLng.lng]))
        const to = g.pointToCellFloat(g.conv.toLocal([e.latlng.lat, e.latlng.lng]))
        const delta = [Math.round(to[0] - from[0]), Math.round(to[1] - from[1])]
        if (delta[0] !== drag.delta[0] || delta[1] !== drag.delta[1]) {
          drag.delta = delta
          const { selection: sel } = stateRef.current
          panelIndexRef.current.forEach((poly, key) => {
            if (!sel.has(key)) return
            const [i, j] = parseKey(key)
            poly.setLatLngs(g.cellPolygon(i + delta[0], j + delta[1]))
          })
        }
      }
    })

    function endDrag() {
      const drag = dragRef.current
      if (!drag) return
      dragRef.current = null
      map.dragging.enable()
      const [di, dj] = drag.delta
      const { grid: g, geo: gg, cells: cs, selection: sel } = stateRef.current
      if ((!di && !dj) || !g || !gg) return
      justDraggedRef.current = true
      setTimeout(() => { justDraggedRef.current = false }, 150)
      const still = cs.filter(([i, j]) => !sel.has(cellKey(i, j)))
      const stillKeys = new Set(still.map(([i, j]) => cellKey(i, j)))
      const moved = [...sel].map(parseKey).map(([i, j]) => [i + di, j + dj])
      const valid = moved.every(([i, j]) => !stillKeys.has(cellKey(i, j)) && cellFits(g, i, j, gg.roofLocal, gg.exclusionsLocal))
      if (valid) {
        commitCells([...still, ...moved], new Set(moved.map(([i, j]) => cellKey(i, j))))
      } else {
        toast('warning', 'Movimiento no válido', 'Los paneles chocarían o quedarían fuera de la cubierta')
        panelIndexRef.current.forEach((poly, key) => {
          if (!sel.has(key)) return
          const [i, j] = parseKey(key)
          poly.setLatLngs(g.cellPolygon(i, j))
        })
      }
    }
    window.addEventListener('mouseup', endDrag)

    mapRef.current = map
    const raf = requestAnimationFrame(() => map.invalidateSize())
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('mouseup', endDrag)
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !catastroRef.current) return
    if (showCatastro) catastroRef.current.addTo(map)
    else catastroRef.current.remove()
  }, [showCatastro])

  useEffect(() => {
    const layer = heatLayerRef.current
    if (!layer) return
    layer.clearLayers()
    if (!heatData || !grid) return
    const span = heatData.max - heatData.min
    heatData.values.forEach(({ i, j, v }) => {
      const t = span > 1e-9 ? (v - heatData.min) / span : 0.5
      L.polygon(grid.cellPolygon(i, j), { weight: 0, fillColor: heatColor(t), fillOpacity: 0.7, interactive: false }).addTo(layer)
    })
  }, [heatData, grid])

  useEffect(() => {
    const layer = roofLayerRef.current
    const vertexLayer = vertexLayerRef.current
    if (!layer || !vertexLayer) return
    layer.clearLayers()
    vertexLayer.clearLayers()
    if (roof.length >= 3) {
      L.polygon(roof, { ...STYLE_ROOF, interactive: false }).addTo(layer)
      roof.forEach((p, idx) => {
        const marker = L.marker(p, { icon: VERTEX_ICON, draggable: true, keyboard: false }).addTo(vertexLayer)
        marker.on('drag', (e) => {
          const next = roof.map((q, n) => (n === idx ? [e.latlng.lat, e.latlng.lng] : q))
          layer.clearLayers()
          L.polygon(next, { ...STYLE_ROOF, interactive: false }).addTo(layer)
        })
        marker.on('dragend', (e) => {
          const ll = e.target.getLatLng()
          setRoof((prev) => prev.map((q, n) => (n === idx ? [ll.lat, ll.lng] : q)))
          setTimeout(() => pruneCells(), 0)
        })
      })
    }
  }, [roof])

  useEffect(() => {
    const layer = exclusionLayerRef.current
    if (!layer) return
    layer.clearLayers()
    exclusions.forEach((poly, idx) => {
      L.polygon(poly, STYLE_EXCLUSION)
        .on('contextmenu', (e) => {
          L.DomEvent.stop(e)
          setExclusions((list) => list.filter((_, n) => n !== idx))
        })
        .addTo(layer)
    })
  }, [exclusions])

  useEffect(() => {
    const layer = obstacleLayerRef.current
    if (!layer || !origin) return
    layer.clearLayers()
    const conv = localConverter(origin)
    const winterNoon = sunVector(Number(lat) || 40, -23.45, 0)
    obstacles.forEach((o, idx) => {
      if (winterNoon[2] > 0.02 && o.height_m > 0) {
        const fx = -winterNoon[0] / winterNoon[2] * o.height_m
        const fy = -winterNoon[1] / winterNoon[2] * o.height_m
        const local = o.poly.map(conv.toLocal)
        const swept = []
        for (const [x, y] of local) {
          swept.push([x, y])
          swept.push([x + fx, y + fy])
        }
        const hull = convexHull(swept).map(conv.toLatLng)
        L.polygon(hull, STYLE_SHADOW).addTo(layer)
      }
      L.polygon(o.poly, STYLE_OBSTACLE)
        .bindTooltip(`Obstáculo · ${o.height_m} m`, { sticky: true })
        .on('contextmenu', (e) => {
          L.DomEvent.stop(e)
          setObstacles((list) => list.filter((_, n) => n !== idx))
        })
        .addTo(layer)
    })
  }, [obstacles, origin, lat])

  useEffect(() => {
    const layer = panelLayerRef.current
    if (!layer || !grid) return
    layer.clearLayers()
    panelIndexRef.current = new Map()
    cells.forEach(([i, j]) => {
      const key = cellKey(i, j)
      const selected = selection.has(key)
      const sIdx = stringIndex?.get(key)
      const style = selected ? STYLE_PANEL_SELECTED
        : sIdx != null ? { ...STYLE_PANEL, fillColor: STRING_COLORS[sIdx % STRING_COLORS.length] }
        : STYLE_PANEL
      const poly = L.polygon(grid.cellPolygon(i, j), style)
      if (sIdx != null) poly.bindTooltip(`Cadena ${sIdx + 1}`, { sticky: true })
      poly.on('click', (e) => { L.DomEvent.stop(e); onPanelClick(key, e) })
      poly.on('mousedown', (e) => beginPanelDrag(key, e))
      poly.addTo(layer)
      panelIndexRef.current.set(key, poly)
    })
  }, [cells, selection, grid, stringIndex])

  useEffect(() => {
    function onKey(e) {
      if (isTyping(e)) return
      const meta = e.metaKey || e.ctrlKey
      if (e.key === 'Escape') {
        e.preventDefault()
        if (stateRef.current.mode !== 'idle') cancelDraft()
        else setSelection(new Set())
      } else if ((e.key === 'Delete' || e.key === 'Backspace') && stateRef.current.selection.size) {
        e.preventDefault()
        deleteSelection()
      } else if (meta && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault()
        copySelection()
      } else if (meta && (e.key === 'v' || e.key === 'V')) {
        e.preventDefault()
        pasteClipboard()
      } else if (meta && (e.key === 'a' || e.key === 'A')) {
        e.preventDefault()
        selectAll()
      } else if (e.key === 'Enter' && stateRef.current.mode !== 'idle') {
        e.preventDefault()
        finishDraft()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const hasCoords = lat !== '' && lat != null && lon !== '' && lon != null
  if (!hasCoords) {
    return (
      <div className="sun-inline-note">
        <Icon name="map-pin" size={14} /> Fija las coordenadas del proyecto en «Datos del lugar» para situar la cubierta.
      </div>
    )
  }
  if (!panel?.width || !panel?.height) {
    return (
      <div className="sun-inline-note">
        <Icon name="package" size={14} /> El panel seleccionado no tiene dimensiones (ancho × alto). Complétalas en la biblioteca de equipos.
      </div>
    )
  }

  const placed = cells.length
  const required = requiredPanels || 0
  const short = required > 0 && placed > 0 && placed < required
  const kwp = panel?.power ? (placed * panel.power) / 1000 : null
  const roofArea = geo && geo.roofLocal.length >= 3 ? polygonAreaM2(geo.roofLocal) : null
  const drawing = mode !== 'idle'

  return (
    <div className="pl-root">
      <div className="pl-toolbar" role="toolbar" aria-label="Herramientas de disposición">
        <Btn variant={mode === 'draw-roof' ? 'primary' : 'secondary'} icon="pencil"
          onClick={() => (mode === 'draw-roof' ? cancelDraft() : setMode('draw-roof'))}>
          {roof.length ? 'Redibujar cubierta' : 'Dibujar cubierta'}
        </Btn>
        <Btn variant={mode === 'draw-exclusion' ? 'primary' : 'secondary'} icon="ban" disabled={roof.length < 3}
          onClick={() => (mode === 'draw-exclusion' ? cancelDraft() : setMode('draw-exclusion'))}>
          Exclusión
        </Btn>
        <Btn variant={mode === 'draw-obstacle' ? 'primary' : 'secondary'} icon="mountain" disabled={roof.length < 3}
          onClick={() => (mode === 'draw-obstacle' ? cancelDraft() : setMode('draw-obstacle'))}
          title="Chimenea, árbol o edificio: proyecta sombra según su altura">
          Obstáculo
        </Btn>
        {mode === 'draw-obstacle' && (
          <label className="pl-gap">
            Altura
            <input className="sun-input num" type="number" min="0.1" step="0.1" value={obstacleHeight}
              onChange={(e) => setObstacleHeight(e.target.value)} />
            m
          </label>
        )}
        <Btn variant={mode === 'measure-azimut' ? 'primary' : 'secondary'} icon="ruler" disabled={roof.length < 3}
          onClick={() => (mode === 'measure-azimut' ? cancelDraft() : setMode('measure-azimut'))}
          title="Orienta las filas midiendo una línea del mapa: dos clics sobre la cumbrera o el alero y un tercero hacia donde miran las filas">
          Medir orientación
        </Btn>
        <Btn variant="secondary" icon="sparkles" disabled={roof.length < 3 || drawing} onClick={autoLayout}>
          Auto-disposición
        </Btn>
        <Btn variant={showHeatmap ? 'primary' : 'secondary'} icon="sun" disabled={roof.length < 3}
          onClick={() => setShowHeatmap((v) => !v)}
          title="Irradiancia anual estimada por celda, descontando la sombra de los obstáculos">
          Mapa solar
        </Btn>
        {rotation != null && (
          <label className="pl-gap" title="Rotación de las filas en pasos de 5°">
            Filas
            <input className="sun-input num" type="number" min="0" max="355" step="5"
              value={Math.round(rotation)}
              onChange={(e) => setRotation(((Number(e.target.value) || 0) % 360 + 360) % 360)} />
            °
            <button type="button" className="pl-seg__opt" title="Volver a la orientación automática"
              onClick={() => { setRotation(null); setPhase(null) }}>
              <Icon name="rotate-ccw" size={12} />
            </button>
          </label>
        )}
        <Btn variant="secondary" icon="trash-2" disabled={selection.size === 0} onClick={deleteSelection}>
          Eliminar{selection.size > 1 ? ` (${selection.size})` : ''}
        </Btn>
        <div className="pl-seg" role="group" aria-label="Orientación del panel">
          <button type="button" className={`pl-seg__opt${orientation === 'v' ? ' pl-seg__opt--on' : ''}`}
            onClick={() => setOrientation('v')} title="Panel en vertical (retrato)">
            <Icon name="rectangle-vertical" size={14} /> Vertical
          </button>
          <button type="button" className={`pl-seg__opt${orientation === 'h' ? ' pl-seg__opt--on' : ''}`}
            onClick={() => setOrientation('h')} title="Panel en horizontal (apaisado)">
            <Icon name="rectangle-horizontal" size={14} /> Horizontal
          </button>
        </div>
        {!coplanar && (
          <label className="pl-gap">
            Separación filas
            <input className="sun-input num" type="number" min="0" step="0.05" placeholder={grid ? grid.gapRow.toFixed(2) : 'auto'}
              value={gapDraft}
              onChange={(e) => {
                setGapDraft(e.target.value)
                setRowGapOverride(e.target.value === '' ? null : Math.max(0, Number(e.target.value) || 0))
              }} />
            m
          </label>
        )}
        <span className="pl-spacer" />
        {placed > 0 && (
          <span className={`pl-chip${short ? ' pl-chip--warn' : ' pl-chip--ok'}`}>
            <Icon name={short ? 'alert-triangle' : 'check'} size={13} />
            {placed}{required ? ` / ${required}` : ''} paneles{kwp != null ? ` · ${kwp.toLocaleString('es-ES', { maximumFractionDigits: 2 })} kWp` : ''}
          </span>
        )}
        {roofArea != null && <span className="pl-chip">{Math.round(roofArea)} m²</span>}
        {stringGroups && (
          <span className="pl-chip">
            {stringGroups.map((keys, idx) => (
              <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: 3, marginRight: idx < stringGroups.length - 1 ? 6 : 0 }}>
                <span style={{ width: 9, height: 9, borderRadius: 2, background: STRING_COLORS[idx % STRING_COLORS.length], display: 'inline-block' }} />
                {keys.length}
              </span>
            ))}
            cadenas
          </span>
        )}
      </div>

      {drawing && (
        <div className="pl-drawhint">
          <Icon name="mouse-pointer-click" size={13} />
          {mode === 'draw-roof' && 'Marca los vértices de la cubierta con clics. Cierra con doble clic, Enter o pulsando el primer vértice · Esc cancela'}
          {mode === 'draw-exclusion' && 'Marca la zona donde no se puede colocar (claraboyas, registros). Cierra con doble clic · Esc cancela'}
          {mode === 'draw-obstacle' && `Marca el contorno del obstáculo (${obstacleHeight || 2} m de alto): chimenea, árbol, edificio vecino. Puede estar fuera de la cubierta. Cierra con doble clic · Esc cancela`}
          {mode === 'measure-azimut' && 'Clic 1 y 2 sobre una línea real del edificio (cumbrera, alero, peto) · clic 3 hacia el lado al que deben mirar las filas'}
        </div>
      )}
      {showHeatmap && heatData && (
        <div className="pl-drawhint">
          <Icon name="sun" size={13} />
          Irradiancia anual estimada
          <span style={{
            display: 'inline-block', width: 110, height: 10, borderRadius: 3,
            background: `linear-gradient(90deg, ${HEAT_RAMP.join(',')})`,
            margin: '0 6px', verticalAlign: 'middle',
          }} />
          {Math.round(heatData.min)} – {Math.round(heatData.max)} {heatData.unit}
        </div>
      )}
      {short && !drawing && (
        <div className="sun-inline-note" style={{ marginBottom: 'var(--space-2)' }}>
          <Icon name="alert-triangle" size={14} /> Caben {placed} de los {required} paneles que requiere el análisis. Amplía la cubierta, cambia la orientación o revisa el diseño.
        </div>
      )}

      <div className={`pl-frame${drawing ? ' pl-frame--drawing' : ''}`}>
        <div ref={mapEl} className="pl-canvas" />
      </div>

      <div className="pl-hints">
        <label className="sun-check pl-catastro">
          <input type="checkbox" checked={showCatastro} onChange={(e) => setShowCatastro(e.target.checked)} />
          <span className="sun-check__box"><Icon name="check" size={11} /></span>
          <span>Parcela catastral</span>
        </label>
        <span className="pl-hints__keys">
          <kbd>clic</kbd> seleccionar · <kbd>⇧ clic</kbd> multiselección · <kbd>⇧ clic</kbd> en hueco = rellenar hasta ahí ·
          <kbd>⌘C</kbd>/<kbd>⌘V</kbd> copiar y pegar · <kbd>⌘A</kbd> todos · <kbd>Supr</kbd> eliminar · arrastra para mover · clic derecho quita un obstáculo
        </span>
      </div>
    </div>
  )
}

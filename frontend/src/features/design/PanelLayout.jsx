import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Btn, Icon } from '@/shared/ui'
import { toast } from '@/services/toast'
import {
  makeGrid, localConverter, cellFits, cellKey, parseKey,
  autoLayoutCells, fillBetweenCells, polygonAreaM2, centroid,
  optimizeLayout, bearingBetween, sunVector, convexHull,
  assignStrings, allocateStrings, annualShadeFactors, orientationLossPct, normalizeLayout,
  idaeRowGap, rowShadeLossPct,
} from './layoutEngine'
import './panel-layout.css'

const PNOA_URL = 'https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile&version=1.0.0'
  + '&layer=OI.OrthoimageCoverage&style=default&format=image/jpeg'
  + '&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}'
const CATASTRO_URL = 'https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx'

const STYLE_ROOF = { color: '#38bdf8', weight: 2, dashArray: '6 4', fillColor: '#38bdf8', fillOpacity: 0.06 }
const STYLE_ROOF_INACTIVE = { color: '#94a3b8', weight: 1.5, dashArray: '6 4', fillColor: '#94a3b8', fillOpacity: 0.04 }
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

export default function PanelLayout({ lat, lon, azimut, inclinacion, coplanar, betaOptimal, panel, requiredPanels, stringConfig, poaAnnual, layout, onChange, onChangePanel }) {
  const [initial] = useState(() => normalizeLayout(layout))
  const [zones, setZones] = useState(initial.zones)
  const [activeZoneId, setActiveZoneId] = useState(initial.zones[0]?.id || null)
  const [exclusions, setExclusions] = useState(initial.exclusions)
  const [obstacles, setObstacles] = useState(initial.obstacles)
  const [obstacleHeight, setObstacleHeight] = useState('2')
  const [selection, setSelection] = useState(() => new Set())
  const [mode, setMode] = useState('idle')
  const [showCatastro, setShowCatastro] = useState(false)
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [gapDraft, setGapDraft] = useState(() => {
    const g = initial.zones[0]?.rows?.gap_m
    return g != null ? String(g) : ''
  })
  const [editingZoneId, setEditingZoneId] = useState(null)
  const [zoneNameDraft, setZoneNameDraft] = useState('')
  const [deficit, setDeficit] = useState(null)

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

  const activeZone = useMemo(() => zones.find((z) => z.id === activeZoneId) || null, [zones, activeZoneId])

  const zoneCtx = useMemo(() => {
    const map = new Map()
    if (!panel?.width || !panel?.height) return map
    for (const z of zones) {
      if (!z.origin || z.roof.length < 3) continue
      const coplanarZ = !!z.plane?.coplanar
      const betaZ = coplanarZ ? (Number(z.plane?.tilt) || 0) : (Number(betaOptimal) || 0)
      const azimutZ = coplanarZ ? (Number(z.plane?.azimut) || 180) : 180
      const conv = localConverter(z.origin)
      const grid = makeGrid({
        origin: z.origin,
        azimut: azimutZ,
        rotation: z.rows?.rotation ?? undefined,
        phase: z.rows?.phase ?? undefined,
        orientation: z.rows?.orientation || 'v',
        panelWmm: panel.width,
        panelHmm: panel.height,
        beta: betaZ,
        coplanar: coplanarZ,
        lat: Number(lat) || 40,
        rowGap: z.rows?.gap_m ?? null,
        colGap: null,
      })
      map.set(z.id, {
        zone: z,
        grid,
        conv,
        betaZ,
        azimutZ,
        coplanarZ,
        roofLocal: z.roof.map(conv.toLocal),
        exclusionsLocal: exclusions.map((e) => (e.poly || e).map(conv.toLocal)),
        obstaclesLocal: obstacles.map((o) => ({
          poly: o.poly.map(conv.toLocal),
          heightM: o.height_m,
          baseElevationM: o.base_elevation_m ?? null,
          transmittance: o.transmittance ?? 0,
        })),
      })
    }
    return map
  }, [zones, exclusions, obstacles, panel?.width, panel?.height, betaOptimal, lat])

  const stringData = useMemo(() => {
    const n = Number(stringConfig?.n_parallel) || 0
    if (!n || n < 2) return null
    const counts = zones.map((z) => z.cells.length)
    if (!counts.some(Boolean)) return null
    const alloc = allocateStrings(counts, n)
    const byZone = new Map()
    const sizes = []
    let offset = 0
    zones.forEach((z, k) => {
      if (!alloc[k] || !z.cells.length) return
      const groups = assignStrings(z.cells, alloc[k])
      const index = new Map()
      groups.forEach((keys, g) => {
        keys.forEach((key) => index.set(key, offset + g))
        sizes.push(keys.length)
      })
      byZone.set(z.id, { groups, index })
      offset += alloc[k]
    })
    return { byZone, sizes }
  }, [zones, stringConfig?.n_parallel])

  const layoutSummary = useMemo(() => {
    const zonesOut = []
    let placedTotal = 0
    let shadeAcc = 0
    let orientAcc = 0
    for (const z of zones) {
      const ctx = zoneCtx.get(z.id)
      if (!ctx || !z.cells.length) continue
      const factors = annualShadeFactors(ctx.grid, z.cells, ctx.obstaclesLocal, Number(lat) || 40)
      const shade = z.cells.reduce((s, [i, j]) => s + (factors.get(cellKey(i, j)) || 0), 0) / z.cells.length
      const rot = z.rows?.rotation
      const orient = ctx.coplanarZ || rot == null ? 0 : orientationLossPct(rot, ctx.azimutZ)
      zonesOut.push({
        zone: z.name,
        placed_panels: z.cells.length,
        shade_loss_pct: Math.round(shade * 1000) / 10,
        tilt: ctx.coplanarZ ? ctx.betaZ : null,
        azimut: ctx.coplanarZ ? ctx.azimutZ : (rot ?? 180),
      })
      placedTotal += z.cells.length
      shadeAcc += shade * z.cells.length
      orientAcc += orient * z.cells.length
    }
    if (!placedTotal) return null
    return {
      placed_panels: placedTotal,
      shade_loss_pct: Math.round((shadeAcc / placedTotal) * 1000) / 10,
      orientation_loss_pct: Math.round((orientAcc / placedTotal) * 10) / 10,
      zones: zonesOut,
    }
  }, [zones, zoneCtx, lat])

  const heatData = useMemo(() => {
    if (!showHeatmap) return null
    const values = []
    let min = Infinity
    let max = -Infinity
    const poa = Number(poaAnnual) || null
    for (const z of zones) {
      const ctx = zoneCtx.get(z.id)
      if (!ctx || ctx.roofLocal.length < 3) continue
      const fit = autoLayoutCells(ctx.grid, ctx.roofLocal, ctx.exclusionsLocal)
      if (!fit.length) continue
      const factors = annualShadeFactors(ctx.grid, fit, ctx.obstaclesLocal, Number(lat) || 40)
      for (const [i, j] of fit) {
        const f = factors.get(cellKey(i, j)) || 0
        const v = poa ? poa * (1 - f) : (1 - f) * 100
        if (v < min) min = v
        if (v > max) max = v
        values.push({ zoneId: z.id, i, j, v })
      }
    }
    if (!values.length) return null
    return { values, min, max, unit: poa ? 'kWh/m²·año' : '% de sol anual' }
  }, [showHeatmap, zones, zoneCtx, lat, poaAnnual])

  stateRef.current = {
    zones, activeZoneId, exclusions, obstacles, obstacleHeight, selection, mode, zoneCtx,
    props: { azimut, inclinacion, coplanar },
  }

  function activeCtx() {
    const s = stateRef.current
    return s.zoneCtx.get(s.activeZoneId) || null
  }

  function patchZone(id, patch) {
    setZones((zs) => zs.map((z) => (z.id === id ? { ...z, ...patch } : z)))
  }

  function patchActiveRows(patch) {
    const s = stateRef.current
    if (!s.activeZoneId) return
    setZones((zs) => zs.map((z) => (z.id === s.activeZoneId ? { ...z, rows: { ...z.rows, ...patch } } : z)))
  }

  function commitCells(zoneId, next, nextSelection) {
    patchZone(zoneId, { cells: next })
    if (nextSelection) setSelection(nextSelection)
    setDeficit(null)
  }

  function addZone(roofPts) {
    const s = stateRef.current
    const idNum = s.zones.reduce((m, z) => Math.max(m, Number(String(z.id).replace(/\D/g, '')) || 0), 0) + 1
    const p = s.props
    const zone = {
      id: `z${idNum}`,
      name: `Zona ${idNum}`,
      roof: roofPts,
      origin: centroid(roofPts),
      plane: {
        azimut: Number(p.azimut) || 180,
        tilt: p.coplanar ? (Number(p.inclinacion) || null) : null,
        coplanar: !!p.coplanar,
      },
      rows: { rotation: null, orientation: 'v', gap_m: null, phase: null },
      cells: [],
    }
    setZones((zs) => [...zs, zone])
    setActiveZoneId(zone.id)
    setSelection(new Set())
    setGapDraft('')
  }

  function removeZone(id) {
    const s = stateRef.current
    const rest = s.zones.filter((z) => z.id !== id)
    setZones(rest)
    if (s.activeZoneId === id) {
      setActiveZoneId(rest[0]?.id || null)
      setSelection(new Set())
      const g = rest[0]?.rows?.gap_m
      setGapDraft(g != null ? String(g) : '')
    }
  }

  function activateZone(id) {
    const s = stateRef.current
    if (s.activeZoneId === id) return
    setActiveZoneId(id)
    setSelection(new Set())
    setDeficit(null)
    const g = s.zones.find((z) => z.id === id)?.rows?.gap_m
    setGapDraft(g != null ? String(g) : '')
  }

  useEffect(() => {
    if (zones.length && zones.length >= 4) {
      const withCells = zones.filter((z) => z.cells.length).length
      const n = Number(stringConfig?.n_parallel) || 0
      if (n && withCells > n) {
        toast('warning', 'Más zonas con paneles que cadenas', `Hay ${withCells} zonas con módulos y solo ${n} cadenas: alguna zona quedará sin cadena asignada`)
      }
    }
  }, [zones.length])

  function finishDraft() {
    const draft = draftRef.current
    const { mode: m, activeZoneId: active, zones: zs } = stateRef.current
    if (draft.length >= 3) {
      const pts = draft.map((p) => [p[0], p[1]])
      if (m === 'draw-roof') {
        if (!active || !zs.length) {
          addZone(pts)
        } else {
          setZones((list) => list.map((z) => (z.id === active
            ? { ...z, roof: pts, origin: z.origin || centroid(pts), cells: [] }
            : z)))
          setSelection(new Set())
        }
      } else if (m === 'draw-zone') {
        addZone(pts)
      } else if (m === 'draw-exclusion') {
        setExclusions((list) => [...list, { poly: pts }])
      } else if (m === 'draw-obstacle') {
        const h = Math.max(0.1, Number(stateRef.current.obstacleHeight) || 2)
        setObstacles((list) => [...list, { poly: pts, height_m: h }])
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
    patchActiveRows({ rotation: rot })
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
    const s = stateRef.current
    const zone = s.zones.find((z) => z.id === s.activeZoneId)
    if (!zone) return
    setSelection(new Set(zone.cells.map(([i, j]) => cellKey(i, j))))
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
    const ctx = activeCtx()
    if (!clip || !clip.length || !ctx) return
    const cs = ctx.zone.cells
    const at = mouseLatLngRef.current
    let base
    if (at) {
      base = ctx.grid.latLngToCell([at.lat, at.lng])
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
      if (!cellFits(ctx.grid, i, j, ctx.roofLocal, ctx.exclusionsLocal)) continue
      occupied.add(key)
      placed.push([i, j])
    }
    if (!placed.length) {
      toast('warning', 'No hay sitio libre ahí', 'Apunta con el ratón a una zona libre de la cubierta y vuelve a pegar')
      return
    }
    commitCells(ctx.zone.id, [...cs, ...placed], new Set(placed.map(([i, j]) => cellKey(i, j))))
  }

  function deleteSelection() {
    const s = stateRef.current
    const zone = s.zones.find((z) => z.id === s.activeZoneId)
    if (!s.selection.size || !zone) return
    commitCells(zone.id, zone.cells.filter(([i, j]) => !s.selection.has(cellKey(i, j))), new Set())
  }

  function autoLayout() {
    const ctx = activeCtx()
    if (!ctx || ctx.roofLocal.length < 3 || !panel?.width || !panel?.height) return
    const s = stateRef.current
    const placedElsewhere = s.zones.reduce((sum, z) => (z.id === ctx.zone.id ? sum : sum + z.cells.length), 0)
    const req = Math.max(0, (Number(requiredPanels) || 0) - placedElsewhere)
    const best = optimizeLayout({
      origin: ctx.zone.origin,
      moduleAzimut: ctx.azimutZ,
      coplanar: ctx.coplanarZ,
      panelWmm: panel.width,
      panelHmm: panel.height,
      beta: ctx.betaZ,
      lat: Number(lat) || 40,
      rowGap: ctx.zone.rows?.gap_m ?? null,
      colGap: null,
      roofLocal: ctx.roofLocal,
      exclusionsLocal: ctx.exclusionsLocal,
      obstaclesLocal: ctx.obstaclesLocal,
      required: req,
    })
    if (!best) {
      toast('warning', 'No cabe ningún panel', 'Revisa la cubierta y las exclusiones')
      return
    }
    setZones((zs) => zs.map((z) => (z.id === ctx.zone.id
      ? { ...z, rows: { ...z.rows, rotation: best.rotation, phase: best.phase, orientation: best.orientation }, cells: best.cells }
      : z)))
    setSelection(new Set())

    const shaded = best.cells.filter(([i, j]) => (best.shadeScores.get(cellKey(i, j)) || 0) > 0.25).length
    const bits = [`retícula a ${Math.round(best.rotation)}°`]
    if (!ctx.coplanarZ && best.lossPct > 0.05) bits.push(`coste de orientación ${best.lossPct.toFixed(1)}%`)
    if (shaded) bits.push(`${shaded} con sombra parcial de obstáculos`)
    if (req > 0 && best.fit.length > req) {
      setDeficit(null)
      toast('success', `${best.cells.length} paneles colocados`, `Caben ${best.fit.length}; ${bits.join(' · ')}`)
    } else if (req > 0 && best.cells.length < req) {
      setDeficit(buildDeficit(ctx, req, best))
    } else {
      setDeficit(null)
      toast('success', `${best.cells.length} paneles colocados`, bits.join(' · '))
    }
  }

  function buildDeficit(ctx, req, best) {
    const latN = Number(lat) || 40
    const base = {
      origin: ctx.zone.origin,
      moduleAzimut: ctx.azimutZ,
      coplanar: ctx.coplanarZ,
      panelWmm: panel.width,
      panelHmm: panel.height,
      beta: ctx.betaZ,
      lat: latN,
      colGap: null,
      roofLocal: ctx.roofLocal,
      exclusionsLocal: ctx.exclusionsLocal,
      obstaclesLocal: ctx.obstaclesLocal,
      required: req,
    }
    const out = { zoneId: ctx.zone.id, req, placed: best.cells.length }

    if (!ctx.coplanarZ) {
      const lengthM = (best.orientation === 'h' ? panel.width : panel.height) / 1000
      const currentGap = ctx.zone.rows?.gap_m ?? Math.max(0.02, idaeRowGap(lengthM, ctx.betaZ, latN))
      const tightGap = Math.round(Math.max(0.02, currentGap / 2) * 100) / 100
      if (tightGap < currentGap - 0.01) {
        const tight = optimizeLayout({ ...base, rowGap: tightGap, orientationChoices: [best.orientation] })
        if (tight && tight.cells.length > best.cells.length) {
          const extraLoss = Math.max(0, rowShadeLossPct(lengthM, ctx.betaZ, tightGap, latN, tight.rotation)
            - rowShadeLossPct(lengthM, ctx.betaZ, currentGap, latN, best.rotation))
          out.tighten = {
            gain: tight.cells.length - best.cells.length,
            lossPct: Math.round(extraLoss * 10) / 10,
            gap: tightGap,
            variant: tight,
          }
        }
      }
    }

    const other = best.orientation === 'v' ? 'h' : 'v'
    const flipped = optimizeLayout({ ...base, rowGap: ctx.zone.rows?.gap_m ?? null, orientationChoices: [other] })
    if (flipped && flipped.cells.length > best.cells.length) {
      out.reorient = { orientation: other, count: flipped.cells.length, variant: flipped }
    }

    if (Number(panel?.power) > 0 && best.fit.length > 0) {
      const minW = Math.ceil((Number(panel.power) * req) / best.fit.length / 5) * 5
      if (minW > Number(panel.power)) out.repower = { minW, nowW: Number(panel.power), fits: best.fit.length }
    }
    return out
  }

  function openDeficitOptions() {
    const ctx = activeCtx()
    if (!ctx || !panel?.width || !panel?.height) return
    const s = stateRef.current
    const placedElsewhere = s.zones.reduce((sum, z) => (z.id === ctx.zone.id ? sum : sum + z.cells.length), 0)
    const req = Math.max(0, (Number(requiredPanels) || 0) - placedElsewhere)
    if (!req) return
    const fit = autoLayoutCells(ctx.grid, ctx.roofLocal, ctx.exclusionsLocal)
    setDeficit(buildDeficit(ctx, req, {
      cells: ctx.zone.cells,
      fit,
      orientation: ctx.zone.rows?.orientation || 'v',
      rotation: ctx.grid.rotation,
    }))
  }

  function applyVariant(zoneId, variant, gapM) {
    setZones((zs) => zs.map((z) => (z.id === zoneId
      ? {
        ...z,
        rows: {
          ...z.rows,
          rotation: variant.rotation,
          phase: variant.phase,
          orientation: variant.orientation,
          ...(gapM != null ? { gap_m: gapM } : {}),
        },
        cells: variant.cells,
      }
      : z)))
    if (gapM != null) setGapDraft(String(gapM))
    setSelection(new Set())
    setDeficit(null)
    toast('success', `${variant.cells.length} paneles colocados`)
  }

  function fillTo(targetLatLng) {
    const s = stateRef.current
    const ctx = activeCtx()
    if (!ctx || !s.selection.size) return
    const anchorKey = [...s.selection][s.selection.size - 1]
    const anchor = parseKey(anchorKey)
    const target = ctx.grid.latLngToCell(targetLatLng)
    const occupied = new Set(ctx.zone.cells.map(([i, j]) => cellKey(i, j)))
    const added = fillBetweenCells(ctx.grid, anchor, target, ctx.roofLocal, ctx.exclusionsLocal, occupied)
    if (!added.length) return
    commitCells(ctx.zone.id, [...ctx.zone.cells, ...added], new Set([...s.selection, ...added.map(([i, j]) => cellKey(i, j))]))
  }

  function onPanelClick(zoneId, key, ev) {
    if (justDraggedRef.current) {
      justDraggedRef.current = false
      return
    }
    if (stateRef.current.mode !== 'idle') {
      draftRef.current = [...draftRef.current, [ev.latlng.lat, ev.latlng.lng]]
      redrawDraft()
      return
    }
    if (zoneId !== stateRef.current.activeZoneId) {
      activateZone(zoneId)
      setSelection(new Set([key]))
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
    let removed = 0
    const next = zones.map((z) => {
      const ctx = zoneCtx.get(z.id)
      if (!ctx || !z.cells.length) return z
      const kept = z.cells.filter(([i, j]) => cellFits(ctx.grid, i, j, ctx.roofLocal, ctx.exclusionsLocal))
      if (kept.length === z.cells.length) return z
      removed += z.cells.length - kept.length
      return { ...z, cells: kept }
    })
    if (removed) {
      toast('info', 'Disposición ajustada', `${removed} panel(es) ya no cabían y se retiraron`)
      setSelection(new Set())
      setZones(next)
    }
  }, [zoneCtx])

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
      if (m === 'draw-roof' || m === 'draw-zone' || m === 'draw-exclusion' || m === 'draw-obstacle') {
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
      if (m === 'draw-roof' || m === 'draw-zone' || m === 'draw-exclusion' || m === 'draw-obstacle') finishDraft()
    })

    map.on('mousemove', (e) => {
      mouseLatLngRef.current = e.latlng
      const { mode: m } = stateRef.current
      if (m === 'draw-roof' || m === 'draw-zone' || m === 'draw-exclusion' || m === 'draw-obstacle' || m === 'measure-azimut') {
        if (draftRef.current.length) redrawDraft([e.latlng.lat, e.latlng.lng])
        return
      }
      const drag = dragRef.current
      const ctx = activeCtx()
      if (drag && ctx) {
        const g = ctx.grid
        const from = g.pointToCellFloat(g.conv.toLocal([drag.startLatLng.lat, drag.startLatLng.lng]))
        const to = g.pointToCellFloat(g.conv.toLocal([e.latlng.lat, e.latlng.lng]))
        const delta = [Math.round(to[0] - from[0]), Math.round(to[1] - from[1])]
        if (delta[0] !== drag.delta[0] || delta[1] !== drag.delta[1]) {
          drag.delta = delta
          const { selection: sel, activeZoneId: active } = stateRef.current
          panelIndexRef.current.forEach((poly, refKey) => {
            const [zid, key] = refKey.split('|')
            if (zid !== active || !sel.has(key)) return
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
      const ctx = activeCtx()
      const { selection: sel } = stateRef.current
      if ((!di && !dj) || !ctx) return
      justDraggedRef.current = true
      setTimeout(() => { justDraggedRef.current = false }, 150)
      const cs = ctx.zone.cells
      const still = cs.filter(([i, j]) => !sel.has(cellKey(i, j)))
      const stillKeys = new Set(still.map(([i, j]) => cellKey(i, j)))
      const moved = [...sel].map(parseKey).map(([i, j]) => [i + di, j + dj])
      const valid = moved.every(([i, j]) => !stillKeys.has(cellKey(i, j)) && cellFits(ctx.grid, i, j, ctx.roofLocal, ctx.exclusionsLocal))
      if (valid) {
        commitCells(ctx.zone.id, [...still, ...moved], new Set(moved.map(([i, j]) => cellKey(i, j))))
      } else {
        toast('warning', 'Movimiento no válido', 'Los paneles chocarían o quedarían fuera de la cubierta')
        panelIndexRef.current.forEach((poly, refKey) => {
          const [zid, key] = refKey.split('|')
          if (zid !== stateRef.current.activeZoneId || !sel.has(key)) return
          const [i, j] = parseKey(key)
          poly.setLatLngs(ctx.grid.cellPolygon(i, j))
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
    if (!heatData) return
    const span = heatData.max - heatData.min
    heatData.values.forEach(({ zoneId, i, j, v }) => {
      const g = zoneCtx.get(zoneId)?.grid
      if (!g) return
      const t = span > 1e-9 ? (v - heatData.min) / span : 0.5
      L.polygon(g.cellPolygon(i, j), { weight: 0, fillColor: heatColor(t), fillOpacity: 0.7, interactive: false }).addTo(layer)
    })
  }, [heatData, zoneCtx])

  useEffect(() => {
    const layer = roofLayerRef.current
    const vertexLayer = vertexLayerRef.current
    if (!layer || !vertexLayer) return
    layer.clearLayers()
    vertexLayer.clearLayers()
    for (const z of zones) {
      if (z.roof.length < 3) continue
      const isActive = z.id === activeZoneId
      const poly = L.polygon(z.roof, isActive
        ? { ...STYLE_ROOF, interactive: false }
        : STYLE_ROOF_INACTIVE)
      if (!isActive) {
        poly.bindTooltip(z.name, { sticky: true })
        poly.on('click', (e) => {
          if (stateRef.current.mode !== 'idle') return
          L.DomEvent.stop(e)
          activateZone(z.id)
        })
      }
      poly.addTo(layer)
      if (!isActive) continue
      z.roof.forEach((p, idx) => {
        const marker = L.marker(p, { icon: VERTEX_ICON, draggable: true, keyboard: false }).addTo(vertexLayer)
        marker.on('drag', (e) => {
          const next = z.roof.map((q, n) => (n === idx ? [e.latlng.lat, e.latlng.lng] : q))
          layer.eachLayer((l) => { if (l === poly) l.setLatLngs(next) })
        })
        marker.on('dragend', (e) => {
          const ll = e.target.getLatLng()
          patchZone(z.id, { roof: z.roof.map((q, n) => (n === idx ? [ll.lat, ll.lng] : q)) })
        })
      })
    }
  }, [zones, activeZoneId])

  useEffect(() => {
    const layer = exclusionLayerRef.current
    if (!layer) return
    layer.clearLayers()
    exclusions.forEach((exc, idx) => {
      L.polygon(exc.poly || exc, STYLE_EXCLUSION)
        .on('contextmenu', (e) => {
          L.DomEvent.stop(e)
          setExclusions((list) => list.filter((_, n) => n !== idx))
        })
        .addTo(layer)
    })
  }, [exclusions])

  useEffect(() => {
    const layer = obstacleLayerRef.current
    if (!layer) return
    layer.clearLayers()
    const winterNoon = sunVector(Number(lat) || 40, -23.45, 0)
    obstacles.forEach((o, idx) => {
      if (winterNoon[2] > 0.02 && o.height_m > 0) {
        const conv = localConverter(centroid(o.poly))
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
  }, [obstacles, lat])

  useEffect(() => {
    const layer = panelLayerRef.current
    if (!layer) return
    layer.clearLayers()
    panelIndexRef.current = new Map()
    for (const z of zones) {
      const ctx = zoneCtx.get(z.id)
      if (!ctx) continue
      const isActive = z.id === activeZoneId
      const zStrings = stringData?.byZone.get(z.id)
      z.cells.forEach(([i, j]) => {
        const key = cellKey(i, j)
        const selected = isActive && selection.has(key)
        const sIdx = zStrings?.index.get(key)
        let style = selected ? STYLE_PANEL_SELECTED
          : sIdx != null ? { ...STYLE_PANEL, fillColor: STRING_COLORS[sIdx % STRING_COLORS.length] }
          : STYLE_PANEL
        if (!isActive) style = { ...style, fillOpacity: 0.5, weight: 1 }
        const poly = L.polygon(ctx.grid.cellPolygon(i, j), style)
        const tip = sIdx != null ? `Cadena ${sIdx + 1}${isActive ? '' : ` · ${z.name}`}` : (isActive ? null : z.name)
        if (tip) poly.bindTooltip(tip, { sticky: true })
        poly.on('click', (e) => { L.DomEvent.stop(e); onPanelClick(z.id, key, e) })
        if (isActive) poly.on('mousedown', (e) => beginPanelDrag(key, e))
        poly.addTo(layer)
        panelIndexRef.current.set(`${z.id}|${key}`, poly)
      })
    }
  }, [zones, selection, zoneCtx, stringData, activeZoneId])

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

  useEffect(() => {
    if (!readyRef.current) { readyRef.current = true; return }
    if (!onChangeRef.current) return
    const hasContent = zones.some((z) => z.roof.length || z.cells.length)
    if (!hasContent) { onChangeRef.current(null); return }
    onChangeRef.current({
      zones: zones.map((z) => ({ ...z, strings: stringData?.byZone.get(z.id)?.groups || null })),
      exclusions,
      obstacles,
      panel: panel ? { w_mm: panel.width, h_mm: panel.height } : null,
      summary: layoutSummary,
    })
  }, [zones, exclusions, obstacles, stringData, layoutSummary])

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

  const placed = zones.reduce((s, z) => s + z.cells.length, 0)
  const required = requiredPanels || 0
  const short = required > 0 && placed > 0 && placed < required
  const kwp = panel?.power ? (placed * panel.power) / 1000 : null
  const roofArea = zones.reduce((s, z) => {
    const ctx = zoneCtx.get(z.id)
    return ctx && ctx.roofLocal.length >= 3 ? s + polygonAreaM2(ctx.roofLocal) : s
  }, 0) || null
  const hasRoof = zones.some((z) => z.roof.length >= 3)
  const drawing = mode !== 'idle'
  const activeGrid = zoneCtx.get(activeZoneId)?.grid || null
  const activeRotation = activeZone?.rows?.rotation ?? null
  const activeOrientation = activeZone?.rows?.orientation || 'v'
  const stringSizes = stringData?.sizes || null

  return (
    <div className="pl-root">
      <div className="pl-toolbar" role="toolbar" aria-label="Herramientas de disposición">
        <Btn variant={mode === 'draw-roof' ? 'primary' : 'secondary'} icon="pencil"
          onClick={() => (mode === 'draw-roof' ? cancelDraft() : setMode('draw-roof'))}>
          {activeZone?.roof?.length ? 'Redibujar cubierta' : 'Dibujar cubierta'}
        </Btn>
        <Btn variant={mode === 'draw-zone' ? 'primary' : 'secondary'} icon="layers" disabled={!hasRoof}
          onClick={() => (mode === 'draw-zone' ? cancelDraft() : setMode('draw-zone'))}
          title="Añade otra agua o superficie con su propia orientación e inclinación">
          Añadir zona
        </Btn>
        <Btn variant={mode === 'draw-exclusion' ? 'primary' : 'secondary'} icon="ban" disabled={!hasRoof}
          onClick={() => (mode === 'draw-exclusion' ? cancelDraft() : setMode('draw-exclusion'))}>
          Exclusión
        </Btn>
        <Btn variant={mode === 'draw-obstacle' ? 'primary' : 'secondary'} icon="mountain" disabled={!hasRoof}
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
        <Btn variant={mode === 'measure-azimut' ? 'primary' : 'secondary'} icon="ruler" disabled={!hasRoof}
          onClick={() => (mode === 'measure-azimut' ? cancelDraft() : setMode('measure-azimut'))}
          title="Orienta las filas midiendo una línea del mapa: dos clics sobre la cumbrera o el alero y un tercero hacia donde miran las filas">
          Medir orientación
        </Btn>
        <Btn variant="secondary" icon="sparkles" disabled={!activeZone || activeZone.roof.length < 3 || drawing} onClick={autoLayout}>
          Auto-disposición
        </Btn>
        <Btn variant={showHeatmap ? 'primary' : 'secondary'} icon="sun" disabled={!hasRoof}
          onClick={() => setShowHeatmap((v) => !v)}
          title="Irradiancia anual estimada por celda, descontando la sombra de los obstáculos">
          Mapa solar
        </Btn>
        {activeRotation != null && (
          <label className="pl-gap" title="Rotación de las filas en pasos de 5°">
            Filas
            <input className="sun-input num" type="number" min="0" max="355" step="5"
              value={Math.round(activeRotation)}
              onChange={(e) => patchActiveRows({ rotation: ((Number(e.target.value) || 0) % 360 + 360) % 360 })} />
            °
            <button type="button" className="pl-seg__opt" title="Volver a la orientación automática"
              onClick={() => patchActiveRows({ rotation: null, phase: null })}>
              <Icon name="rotate-ccw" size={12} />
            </button>
          </label>
        )}
        <Btn variant="secondary" icon="trash-2" disabled={selection.size === 0} onClick={deleteSelection}>
          Eliminar{selection.size > 1 ? ` (${selection.size})` : ''}
        </Btn>
        <div className="pl-seg" role="group" aria-label="Orientación del panel">
          <button type="button" className={`pl-seg__opt${activeOrientation === 'v' ? ' pl-seg__opt--on' : ''}`}
            onClick={() => patchActiveRows({ orientation: 'v' })} title="Panel en vertical (retrato)">
            <Icon name="rectangle-vertical" size={14} /> Vertical
          </button>
          <button type="button" className={`pl-seg__opt${activeOrientation === 'h' ? ' pl-seg__opt--on' : ''}`}
            onClick={() => patchActiveRows({ orientation: 'h' })} title="Panel en horizontal (apaisado)">
            <Icon name="rectangle-horizontal" size={14} /> Horizontal
          </button>
        </div>
        {activeZone && !activeZone.plane?.coplanar && (
          <label className="pl-gap">
            Separación filas
            <input className="sun-input num" type="number" min="0" step="0.05" placeholder={activeGrid ? activeGrid.gapRow.toFixed(2) : 'auto'}
              value={gapDraft}
              onChange={(e) => {
                setGapDraft(e.target.value)
                patchActiveRows({ gap_m: e.target.value === '' ? null : Math.max(0, Number(e.target.value) || 0) })
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
        {stringSizes && (
          <span className="pl-chip">
            {stringSizes.map((size, idx) => (
              <span key={idx} style={{ display: 'inline-flex', alignItems: 'center', gap: 3, marginRight: idx < stringSizes.length - 1 ? 6 : 0 }}>
                <span style={{ width: 9, height: 9, borderRadius: 2, background: STRING_COLORS[idx % STRING_COLORS.length], display: 'inline-block' }} />
                {size}
              </span>
            ))}
            cadenas
          </span>
        )}
      </div>

      {zones.length > 0 && (
        <div className="pl-zonebar">
          {zones.map((z) => (
            editingZoneId === z.id ? (
              <input key={z.id} className="sun-input pl-zonebar__rename" autoFocus value={zoneNameDraft}
                onChange={(e) => setZoneNameDraft(e.target.value)}
                onBlur={() => { patchZone(z.id, { name: zoneNameDraft.trim() || z.name }); setEditingZoneId(null) }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') { patchZone(z.id, { name: zoneNameDraft.trim() || z.name }); setEditingZoneId(null) }
                  if (e.key === 'Escape') setEditingZoneId(null)
                }} />
            ) : (
              <button key={z.id} type="button"
                className={`pl-zonebar__chip${z.id === activeZoneId ? ' pl-zonebar__chip--on' : ''}`}
                onClick={() => activateZone(z.id)}
                onDoubleClick={() => { setEditingZoneId(z.id); setZoneNameDraft(z.name) }}
                title="Doble clic para renombrar">
                {z.name}
                <span className="pl-zonebar__count">{z.cells.length}</span>
                {zones.length > 1 && (
                  <span role="button" tabIndex={-1} className="pl-zonebar__close" title="Eliminar zona"
                    onClick={(e) => { e.stopPropagation(); removeZone(z.id) }}>
                    <Icon name="x" size={11} />
                  </span>
                )}
              </button>
            )
          ))}
          {activeZone && (
            <span className="pl-zonebar__plane">
              <label className="sun-check">
                <input type="checkbox" checked={!!activeZone.plane?.coplanar}
                  onChange={(e) => patchZone(activeZone.id, {
                    plane: {
                      ...activeZone.plane,
                      coplanar: e.target.checked,
                      tilt: e.target.checked ? (activeZone.plane?.tilt ?? (Number(inclinacion) || null)) : activeZone.plane?.tilt,
                    },
                  })} />
                <span className="sun-check__box"><Icon name="check" size={11} /></span>
                <span>Coplanar</span>
              </label>
              {activeZone.plane?.coplanar && (
                <>
                  <label className="pl-gap" title="Azimut del agua: 180° = sur">
                    Azimut
                    <input className="sun-input num" type="number" min="0" max="359" step="1"
                      value={activeZone.plane?.azimut ?? 180}
                      onChange={(e) => patchZone(activeZone.id, { plane: { ...activeZone.plane, azimut: ((Number(e.target.value) || 0) % 360 + 360) % 360 } })} />
                    °
                  </label>
                  <label className="pl-gap" title="Inclinación del agua sobre la horizontal">
                    Inclinación
                    <input className="sun-input num" type="number" min="0" max="90" step="1"
                      value={activeZone.plane?.tilt ?? ''}
                      onChange={(e) => patchZone(activeZone.id, { plane: { ...activeZone.plane, tilt: e.target.value === '' ? null : Math.max(0, Math.min(90, Number(e.target.value) || 0)) } })} />
                    °
                  </label>
                </>
              )}
            </span>
          )}
        </div>
      )}

      {drawing && (
        <div className="pl-drawhint">
          <Icon name="mouse-pointer-click" size={13} />
          {mode === 'draw-roof' && 'Marca los vértices de la cubierta con clics. Cierra con doble clic, Enter o pulsando el primer vértice · Esc cancela'}
          {mode === 'draw-zone' && 'Marca los vértices de la nueva zona (otra agua o superficie). Tendrá su propia orientación e inclinación. Cierra con doble clic · Esc cancela'}
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
      {deficit && (
        <div className="pl-deficit">
          <div className="pl-deficit__head">
            <Icon name="alert-triangle" size={15} />
            <strong>Solo caben {deficit.placed} de los {deficit.req} módulos en esta zona</strong>
            <span className="pl-spacer" />
            <button type="button" className="pl-deficit__x" onClick={() => setDeficit(null)} title="Cerrar">
              <Icon name="x" size={13} />
            </button>
          </div>
          <div className="pl-deficit__opts">
            <div className="pl-deficit__opt">
              <div>
                <strong>Añadir otra zona</strong>
                <p>Dibuja otra agua de la cubierta con su propio azimut e inclinación; la producción se calcula zona a zona.</p>
              </div>
              <Btn variant="secondary" icon="layers" onClick={() => { setDeficit(null); setMode('draw-zone') }}>Dibujar zona</Btn>
            </div>
            {deficit.tighten && (
              <div className="pl-deficit__opt">
                <div>
                  <strong>Apretar las filas</strong>
                  <p>+{deficit.tighten.gain} módulos con separación de {deficit.tighten.gap} m · sombra entre filas estimada −{deficit.tighten.lossPct.toFixed(1)} % anual</p>
                </div>
                <Btn variant="secondary" onClick={() => applyVariant(deficit.zoneId, deficit.tighten.variant, deficit.tighten.gap)}>Aplicar</Btn>
              </div>
            )}
            {deficit.reorient && (
              <div className="pl-deficit__opt">
                <div>
                  <strong>Girar los módulos a {deficit.reorient.orientation === 'h' ? 'paisaje' : 'vertical'}</strong>
                  <p>Con la otra rotación caben {deficit.reorient.count} módulos en esta zona.</p>
                </div>
                <Btn variant="secondary" onClick={() => applyVariant(deficit.zoneId, deficit.reorient.variant)}>Aplicar</Btn>
              </div>
            )}
            {deficit.repower && (
              <div className="pl-deficit__opt">
                <div>
                  <strong>Módulo más potente</strong>
                  <p>Con módulos de ≥ {deficit.repower.minW} W (ahora {deficit.repower.nowW} W) los {deficit.repower.fits} que caben cubrirían la potencia del análisis. Cambiar el panel vuelve a Equipos y recalcula el análisis.</p>
                </div>
                <Btn variant="secondary" icon="package" onClick={() => { setDeficit(null); onChangePanel?.() }} disabled={!onChangePanel}>Cambiar panel</Btn>
              </div>
            )}
            <div className="pl-deficit__opt">
              <div>
                <strong>Aceptar menos potencia</strong>
                <p>Continuar con los {placed} módulos colocados: la producción anual y la memoria se recalculan con la disposición real.</p>
              </div>
              <Btn variant="ghost" onClick={() => setDeficit(null)}>Aceptar</Btn>
            </div>
          </div>
        </div>
      )}
      {short && !drawing && !deficit && (
        <div className="sun-inline-note" style={{ marginBottom: 'var(--space-2)' }}>
          <Icon name="alert-triangle" size={14} /> Caben {placed} de los {required} paneles que requiere el análisis.
          <Btn variant="ghost" onClick={openDeficitOptions}>Ver opciones</Btn>
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

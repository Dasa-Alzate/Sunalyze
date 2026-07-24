import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Btn, Icon } from '@/shared/ui'
import { toast } from '@/services/toast'
import {
  makeGrid, localConverter, cellFits, cellKey, parseKey,
  autoLayoutCells, fillBetweenCells, polygonAreaM2, centroid,
} from './layoutEngine'
import './panel-layout.css'

const PNOA_URL = 'https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile&version=1.0.0'
  + '&layer=OI.OrthoimageCoverage&style=default&format=image/jpeg'
  + '&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}'
const CATASTRO_URL = 'https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx'

const STYLE_ROOF = { color: '#38bdf8', weight: 2, dashArray: '6 4', fillColor: '#38bdf8', fillOpacity: 0.06 }
const STYLE_EXCLUSION = { color: '#ef4444', weight: 1.5, dashArray: '4 3', fillColor: '#ef4444', fillOpacity: 0.18 }
const STYLE_PANEL = { color: '#e2e8f0', weight: 1, fillColor: '#0f2c52', fillOpacity: 0.85 }
const STYLE_PANEL_SELECTED = { color: '#f59e0b', weight: 2, fillColor: '#1d4ed8', fillOpacity: 0.9 }
const STYLE_DRAFT = { color: '#38bdf8', weight: 2, dashArray: '4 4' }

const VERTEX_ICON = L.divIcon({ className: 'pl-vertex', iconSize: [11, 11], iconAnchor: [5.5, 5.5] })

function isTyping(e) {
  const el = e.target
  return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable)
}

export default function PanelLayout({ lat, lon, azimut, inclinacion, coplanar, betaOptimal, panel, requiredPanels, layout, onChange }) {
  const [roof, setRoof] = useState(() => layout?.roof || [])
  const [exclusions, setExclusions] = useState(() => layout?.exclusions || [])
  const [cells, setCells] = useState(() => (layout?.cells || []).map(([i, j]) => [i, j]))
  const [orientation, setOrientation] = useState(() => layout?.orientation || 'v')
  const [rowGapOverride, setRowGapOverride] = useState(() => layout?.row_gap_m ?? null)
  const [origin, setOrigin] = useState(() => layout?.origin || null)
  const [selection, setSelection] = useState(() => new Set())
  const [mode, setMode] = useState('idle')
  const [showCatastro, setShowCatastro] = useState(false)
  const [gapDraft, setGapDraft] = useState(() => (layout?.row_gap_m != null ? String(layout.row_gap_m) : ''))

  const mapEl = useRef(null)
  const mapRef = useRef(null)
  const catastroRef = useRef(null)
  const roofLayerRef = useRef(null)
  const vertexLayerRef = useRef(null)
  const exclusionLayerRef = useRef(null)
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
      orientation,
      panelWmm: panel.width,
      panelHmm: panel.height,
      beta,
      coplanar: !!coplanar,
      lat: Number(lat) || 40,
      rowGap: rowGapOverride,
      colGap: null,
    })
  }, [origin, gridAzimut, orientation, panel?.width, panel?.height, beta, coplanar, lat, rowGapOverride])

  const geo = useMemo(() => {
    if (!origin) return null
    const conv = localConverter(origin)
    return {
      conv,
      roofLocal: roof.map(conv.toLocal),
      exclusionsLocal: exclusions.map((poly) => poly.map(conv.toLocal)),
    }
  }, [origin, roof, exclusions])

  stateRef.current = { roof, exclusions, cells, selection, mode, grid, geo, origin }

  useEffect(() => {
    if (!readyRef.current) { readyRef.current = true; return }
    if (!onChangeRef.current) return
    if (!roof.length && !cells.length) { onChangeRef.current(null); return }
    onChangeRef.current({
      roof,
      exclusions,
      cells,
      orientation,
      origin,
      azimut: gridAzimut,
      beta,
      coplanar: !!coplanar,
      row_gap_m: rowGapOverride,
      col_gap_m: null,
      panel: panel ? { w_mm: panel.width, h_mm: panel.height } : null,
    })
  }, [roof, exclusions, cells, orientation, origin, rowGapOverride])

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
      }
    }
    draftRef.current = []
    draftLayerRef.current?.clearLayers()
    setMode('idle')
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
    const style = stateRef.current.mode === 'draw-exclusion' ? STYLE_EXCLUSION : STYLE_DRAFT
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
    const { grid: g, geo: gg } = stateRef.current
    if (!g || !gg || gg.roofLocal.length < 3) return
    const placed = autoLayoutCells(g, gg.roofLocal, gg.exclusionsLocal)
    commitCells(placed, new Set())
    toast('success', `${placed.length} paneles colocados`, requiredPanels ? `El análisis requiere ${requiredPanels}` : undefined)
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
    roofLayerRef.current = L.layerGroup().addTo(map)
    vertexLayerRef.current = L.layerGroup().addTo(map)
    exclusionLayerRef.current = L.layerGroup().addTo(map)
    panelLayerRef.current = L.layerGroup().addTo(map)
    draftLayerRef.current = L.layerGroup().addTo(map)

    map.on('click', (e) => {
      const { mode: m, selection: sel } = stateRef.current
      if (m === 'draw-roof' || m === 'draw-exclusion') {
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
      if (m === 'draw-roof' || m === 'draw-exclusion') finishDraft()
    })

    map.on('mousemove', (e) => {
      mouseLatLngRef.current = e.latlng
      const { mode: m, grid: g } = stateRef.current
      if (m === 'draw-roof' || m === 'draw-exclusion') {
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
    const layer = panelLayerRef.current
    if (!layer || !grid) return
    layer.clearLayers()
    panelIndexRef.current = new Map()
    cells.forEach(([i, j]) => {
      const key = cellKey(i, j)
      const selected = selection.has(key)
      const poly = L.polygon(grid.cellPolygon(i, j), selected ? STYLE_PANEL_SELECTED : STYLE_PANEL)
      poly.on('click', (e) => { L.DomEvent.stop(e); onPanelClick(key, e) })
      poly.on('mousedown', (e) => beginPanelDrag(key, e))
      poly.addTo(layer)
      panelIndexRef.current.set(key, poly)
    })
  }, [cells, selection, grid])

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
  const short = required > 0 && placed < required
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
          Obstáculo
        </Btn>
        <Btn variant="secondary" icon="sparkles" disabled={roof.length < 3 || drawing} onClick={autoLayout}>
          Auto-disposición
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
      </div>

      {drawing && (
        <div className="pl-drawhint">
          <Icon name="mouse-pointer-click" size={13} />
          {mode === 'draw-roof' ? 'Marca los vértices de la cubierta con clics.' : 'Marca los vértices del obstáculo (chimeneas, claraboyas, sombras).'}
          {' '}Cierra con doble clic, Enter o pulsando el primer vértice · Esc cancela
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

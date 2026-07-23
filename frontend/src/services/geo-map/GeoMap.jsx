import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Icon } from '@/shared/ui'
import './geo-map.css'

const SPAIN_CENTER = [40.4168, -3.7038]

const PIN_ICON = L.divIcon({
  className: 'geo-map__pin',
  html: '<span class="geo-map__pin-dot"></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

async function lookup(q) {
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&q=${encodeURIComponent(q)}`,
    { headers: { 'Accept-Language': 'es' } },
  )
  const data = await res.json()
  return data.length ? data[0] : null
}

function locality(q) {
  const parts = q.split(',').map((s) => s.trim()).filter(Boolean)
  const named = parts.filter((p) => !/^\d+$/.test(p))
  const relaxed = named.slice(-1)[0]
  return relaxed && relaxed !== q ? relaxed : null
}

export function GeoMap({ lat, lon, onPick, height = 240 }) {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState(null)
  const [note, setNote] = useState(null)
  const mapEl = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick

  const hasCoords = lat !== '' && lat != null && lon !== '' && lon != null

  useEffect(() => {
    if (!mapEl.current || mapRef.current) return undefined
    const start = hasCoords ? [Number(lat), Number(lon)] : SPAIN_CENTER
    const map = L.map(mapEl.current, { center: start, zoom: hasCoords ? 15 : 5 })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19,
    }).addTo(map)
    map.on('click', (e) => {
      onPickRef.current && onPickRef.current(e.latlng.lat.toFixed(4), e.latlng.lng.toFixed(4))
    })
    mapRef.current = map
    const raf = requestAnimationFrame(() => map.invalidateSize())
    return () => {
      cancelAnimationFrame(raf)
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (!hasCoords) {
      if (markerRef.current) { markerRef.current.remove(); markerRef.current = null }
      return
    }
    const pos = [Number(lat), Number(lon)]
    if (markerRef.current) markerRef.current.setLatLng(pos)
    else markerRef.current = L.marker(pos, { icon: PIN_ICON, keyboard: false }).addTo(map)
    map.setView(pos, Math.max(map.getZoom(), 15))
  }, [lat, lon])

  async function geocode(e) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setSearching(true)
    setError(null)
    setNote(null)
    try {
      const exact = await lookup(q)
      if (exact) {
        onPick && onPick(Number(exact.lat).toFixed(4), Number(exact.lon).toFixed(4), exact.display_name)
        return
      }
      const relaxed = locality(q)
      const approx = relaxed ? await lookup(relaxed) : null
      if (approx) {
        onPick && onPick(Number(approx.lat).toFixed(4), Number(approx.lon).toFixed(4), approx.display_name)
        setNote(`No encontramos la dirección exacta; te situamos en «${relaxed}». Ajusta el pin si hace falta.`)
        return
      }
      setError('Sin resultados en España. Revisa la calle y la localidad, o fija las coordenadas a mano.')
    } catch {
      setError('No se pudo geocodificar (sin conexión)')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="geo-map">
      <form className="geo-map__search" onSubmit={geocode}>
        <div className="sun-input-group" style={{ flex: 1 }}>
          <span className="sun-input-group__icon"><Icon name="search" size={16} /></span>
          <input
            className="sun-input"
            placeholder="Buscar dirección para fijar coordenadas…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button type="submit" className="sun-btn sun-btn--secondary" disabled={searching}>
          <Icon name="map-pin" size={16} />{searching ? 'Buscando…' : 'Localizar'}
        </button>
      </form>
      {error && <div className="geo-map__error"><Icon name="alert-circle" size={13} />{error}</div>}
      {note && <div className="geo-map__note"><Icon name="map-pin" size={13} />{note}</div>}
      <div className="geo-map__frame" style={{ height }}>
        <div ref={mapEl} className="geo-map__canvas" />
      </div>
      <div className="geo-map__hint">
        <Icon name="mouse-pointer-click" size={13} />
        Haz clic en el mapa para fijar el pin{hasCoords && <span className="num"> · {Number(lat).toFixed(4)}, {Number(lon).toFixed(4)}</span>}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Icon } from '@/shared/ui'
import './geo-map.css'

function bbox(lat, lon, delta = 0.025) {
  const la = Number(lat) || 0
  const lo = Number(lon) || 0
  return `${lo - delta},${la - delta},${lo + delta},${la + delta}`
}

export function GeoMap({ lat, lon, onPick, height = 240 }) {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState(null)
  const hasCoords = lat !== '' && lat != null && lon !== '' && lon != null

  async function geocode(e) {
    e.preventDefault()
    if (!query.trim()) return
    setSearching(true)
    setError(null)
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`,
        { headers: { 'Accept-Language': 'es' } },
      )
      const data = await res.json()
      if (!data.length) {
        setError('Sin resultados para esa dirección')
        return
      }
      const { lat: la, lon: lo, display_name } = data[0]
      onPick && onPick(Number(la).toFixed(4), Number(lo).toFixed(4), display_name)
    } catch {
      setError('No se pudo geocodificar (sin conexión)')
    } finally {
      setSearching(false)
    }
  }

  const src = hasCoords
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${bbox(lat, lon)}&layer=mapnik&marker=${lat},${lon}`
    : null

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
      <div className="geo-map__frame" style={{ height }}>
        {src ? (
          <iframe title="Mapa" src={src} loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
        ) : (
          <div className="geo-map__empty">
            <Icon name="map" size={22} />
            <span>Introduce coordenadas o busca una dirección</span>
          </div>
        )}
      </div>
      {hasCoords && (
        <div className="geo-map__coords">
          <Icon name="map-pin" size={13} color="var(--green-600)" />
          <span className="num">{Number(lat).toFixed(4)}, {Number(lon).toFixed(4)}</span>
        </div>
      )}
    </div>
  )
}

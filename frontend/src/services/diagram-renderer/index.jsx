import { useEffect, useState } from 'react'

const UNIFILAR_BASE = '/static/assets/unifilar'

export const DEFAULT_UNIFILAR_NODES = [
  { src: 'panel.svg', label: 'Campo FV' },
  { src: 'fuse.svg', label: 'Fusible' },
  { src: 'inverter.svg', label: 'Inversor' },
  { src: 'diff.svg', label: 'Diferencial' },
  { src: 'MT.svg', label: 'Magnet.' },
]

export function UnifilarStrip({ nodes = DEFAULT_UNIFILAR_NODES, className = '' }) {
  return (
    <div className={`web-uni ${className}`}>
      {nodes.map((n, i) => (
        <span key={n.src} style={{ display: 'contents' }}>
          <span className="web-uni__node">
            <img src={`${UNIFILAR_BASE}/${n.src}`} alt={n.label} />
            <span>{n.label}</span>
          </span>
          {i < nodes.length - 1 && <span className="web-uni__wire" />}
        </span>
      ))}
    </div>
  )
}

export function CircuitSvg({ type = 'cc-strings', params = {}, fallback = null }) {
  const [svg, setSvg] = useState(null)
  const [error, setError] = useState(false)
  const qs = new URLSearchParams(params).toString()

  useEffect(() => {
    let alive = true
    setSvg(null)
    setError(false)
    fetch(`/api/circuit/${type}${qs ? `?${qs}` : ''}`)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((text) => alive && setSvg(text))
      .catch(() => alive && setError(true))
    return () => { alive = false }
  }, [type, qs])

  if (error) return fallback
  if (!svg) return <div className="diagram-renderer__loading">Generando esquema…</div>
  return <div className="diagram-renderer__svg" dangerouslySetInnerHTML={{ __html: svg }} />
}

import { useState, useEffect, useRef } from 'react'
import { Icon } from '@/shared/ui'
import { UnifilarStrip } from '@/services/diagram-renderer'

function ScreenResumen() {
  return (
    <div className="web-shot__body">
      <div className="web-mini-metric">
        <div className="l">Campo FV</div>
        <div className="v">6,60<span> kWp</span></div>
        <div style={{ height: 2, background: 'var(--green-100)', borderRadius: 2, margin: '10px 0 0' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
          <span>12 paneles · 2 × 6</span><span style={{ color: 'var(--green-600)', fontWeight: 600 }}>Válido</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <div className="web-mini-metric" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <div className="l">Irradiancia</div><div className="v" style={{ fontSize: 20 }}>1.847<span> kWh/m²</span></div>
        </div>
        <div className="web-mini-metric" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <div className="l">Producción</div><div className="v" style={{ fontSize: 20 }}>7,9<span> MWh/año</span></div>
        </div>
      </div>
    </div>
  )
}

function ScreenMemoria() {
  return (
    <div className="web-shot__body web-shot__body--solo">
      <div className="web-memo">
        <div className="web-memo__title">Memoria Técnica · Instalación FV</div>
        <div className="web-memo__sub">Juan García López — Alicante</div>
        <div className="web-memo__h">1 · Descripción de la instalación</div>
        <span className="web-memo__line" style={{ width: '100%' }} />
        <span className="web-memo__line" style={{ width: '92%' }} />
        <span className="web-memo__line" style={{ width: '74%' }} />
        <div className="web-memo__h">2 · Cálculos justificativos</div>
        <span className="web-memo__line" style={{ width: '88%' }} />
        <div className="web-memo__chip"><Icon name="check" size={12} /> Conforme ITC-BT-40</div>
      </div>
    </div>
  )
}

function ScreenUnifilar() {
  return (
    <div className="web-shot__body web-shot__body--solo">
      <UnifilarStrip />
    </div>
  )
}

function ScreenProyectos() {
  const rows = [
    { c: 'J. García', k: '6,60', s: 'Memoria', tone: 'success' },
    { c: 'Nave Hnos. Ruiz', k: '48,6', s: 'Diseño', tone: 'warning' },
    { c: 'A. López', k: '3,60', s: 'Borrador', tone: 'neutral' },
  ]
  return (
    <div className="web-shot__body web-shot__body--solo">
      <div className="web-projlist">
        {rows.map((r) => (
          <div className="web-projrow" key={r.c}>
            <div>
              <div className="web-projrow__c">{r.c}</div>
              <div className="web-projrow__k">{r.k} kWp</div>
            </div>
            <span className={`sun-badge sun-badge--${r.tone}`}>{r.s}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const SCREENS = [
  { key: 'resumen', title: 'Resumen del diseño', Comp: ScreenResumen,
    badges: [['file-check-2', 'var(--green-600)', 'Memoria generada', 'PDF + unifilar · ITC-BT-40'], ['shield-check', 'var(--blue-500)', 'Validado por norma', null]] },
  { key: 'memoria', title: 'Memoria técnica', Comp: ScreenMemoria,
    badges: [['file-text', 'var(--green-600)', 'Documento listo', 'Generado al instante'], ['pen-line', 'var(--blue-500)', 'Listo para firmar', null]] },
  { key: 'unifilar', title: 'Esquema unifilar', Comp: ScreenUnifilar,
    badges: [['workflow', 'var(--green-600)', 'Unifilar automático', 'Desde tus equipos'], ['shield-check', 'var(--amber-600)', 'Protecciones DC/AC', null]] },
  { key: 'proyectos', title: 'Mis proyectos', Comp: ScreenProyectos,
    badges: [['folder', 'var(--green-600)', '12 proyectos', 'Diseños + memorias'], ['clock', 'var(--blue-500)', 'Autoguardado', null]] },
]

function FloatBadge({ data, variant }) {
  const [ic, color, title, sub] = data
  return (
    <div className={`web-float-badge${variant === 2 ? ' web-float-badge--2' : ''}`}>
      <Icon name={ic} size={18} color={color} />
      <div style={{ lineHeight: 1.25 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-strong)' }}>{title}</div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-subtle)' }}>{sub}</div>}
      </div>
    </div>
  )
}

export function HeroPreview() {
  const [i, setI] = useState(0)
  const paused = useRef(false)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const id = setInterval(() => { if (!paused.current) setI((v) => (v + 1) % SCREENS.length) }, 3600)
    return () => clearInterval(id)
  }, [])
  const s = SCREENS[i]
  const Comp = s.Comp
  return (
    <div className="web-shot" onMouseEnter={() => { paused.current = true }} onMouseLeave={() => { paused.current = false }}>
      <div className="web-shot__bar">
        <span className="d" style={{ background: '#ff5f57' }} />
        <span className="d" style={{ background: '#febc2e' }} />
        <span className="d" style={{ background: '#28c840' }} />
        <span className="web-shot__bartitle">Sunalyze · {s.title}</span>
      </div>
      <div className="web-shot__stage">
        <div className="web-shot__screen" key={s.key}><Comp /></div>
      </div>
      <div className="web-shot__dots">
        {SCREENS.map((sc, idx) => (
          <button key={sc.key} className={`web-shot__dot${idx === i ? ' on' : ''}`} aria-label={sc.title} onClick={() => setI(idx)} />
        ))}
      </div>
      <FloatBadge data={s.badges[0]} variant={1} />
      <FloatBadge data={s.badges[1]} variant={2} />
    </div>
  )
}

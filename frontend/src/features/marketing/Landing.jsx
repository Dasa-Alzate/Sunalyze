import { useState, useEffect, useRef } from 'react'
import { Btn, Icon } from '@/shared/ui'
import { useTransition } from '@/services/transition'
import { HeroPreview } from './HeroPreview'

function Counter({ to, decimals = 0, suffix = '', prefix = '', dur = 1400 }) {
  const ref = useRef(null)
  const [val, setVal] = useState(0)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { setVal(to); return }
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => {
        if (e.isIntersecting) {
          const t0 = performance.now()
          const tick = (t) => {
            const p = Math.min(1, (t - t0) / dur)
            const eased = 1 - Math.pow(1 - p, 3)
            setVal(to * eased)
            if (p < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
          io.disconnect()
        }
      })
    }, { threshold: 0.4 })
    io.observe(el)
    return () => io.disconnect()
  }, [to])
  const fmt = val.toLocaleString('es-ES', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  return <span ref={ref}>{prefix}{fmt}<span className="u">{suffix}</span></span>
}

function Nav({ go }) {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  return (
    <nav className={`web-nav${scrolled ? ' scrolled' : ''}`}>
      <a className="web-brand" href="#" onClick={(e) => { e.preventDefault(); go('landing') }}>
        <span className="mark"><Icon name="sun" size={18} strokeWidth={2.4} /></span>Sunalyze
      </a>
      <div className="web-nav__links">
        <a href="#features">Funciones</a>
        <a href="#how">Cómo funciona</a>
        <a href="#showcase">Producto</a>
        <a href="#pricing">Precios</a>
      </div>
      <div className="web-nav__spacer" />
      <div className="web-nav__actions">
        <Btn variant="ghost" size="md" onClick={() => go('login')}>Iniciar sesión</Btn>
        <Btn variant="primary" size="md" onClick={() => go('signup')}>Probar gratis</Btn>
      </div>
    </nav>
  )
}

function Hero({ go }) {
  const shotRef = useRef(null)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const onScroll = () => {
      const y = window.scrollY
      if (shotRef.current) shotRef.current.style.transform = `translateY(${y * -0.04}px)`
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  return (
    <header className="web-hero">
      <div className="web-hero__bg">
        <div className="web-hero__mesh" />
        <div className="web-hero__grid-lines" />
      </div>
      <div className="web-wrap web-hero__grid">
        <div className="web-hero__copy">
          <span className="web-eyebrow"><Icon name="zap" size={13} /> Diseño + legalización en un solo flujo</span>
          <h1>De las coordenadas a la <em>memoria técnica firmable</em> en 10 minutos.</h1>
          <p className="web-hero__lead">Dimensiona la instalación, valida cada cálculo contra normativa y genera la memoria y el esquema unifilar. Sin saltar entre PVsyst y Word.</p>
          <div className="web-hero__cta">
            <Btn variant="primary" size="lg" icon="arrow-right" onClick={() => go('signup')}>Empieza gratis</Btn>
            <Btn variant="secondary" size="lg" icon="play" onClick={() => go('login')}>Ver demo</Btn>
          </div>
          <div className="web-hero__note"><Icon name="check-circle-2" size={15} color="var(--green-600)" /> 14 días de prueba · Sin tarjeta · Cancela cuando quieras</div>
        </div>
        <div style={{ position: 'relative' }}>
          <div className="web-hero__sun">
            <div className="web-hero__rays" />
            <div className="web-hero__halo" />
          </div>
          <div ref={shotRef}>
            <HeroPreview />
          </div>
        </div>
      </div>
    </header>
  )
}

function Stats() {
  const items = [
    { v: <Counter to={10} suffix=" min" />, l: 'De coordenadas a memoria' },
    { v: <Counter to={4200} suffix="+" />, l: 'Memorias generadas' },
    { v: <Counter to={148} decimals={0} suffix=" MWp" />, l: 'Potencia diseñada' },
    { v: <Counter to={99.9} decimals={1} suffix=" %" />, l: 'Cálculos conformes' },
  ]
  return (
    <section className="web-stats">
      <div className="web-stats__grid">
        {items.map((s, i) => (
          <div className="web-stat reveal" data-d={i + 1} key={i}>
            <div className="web-stat__v">{s.v}</div>
            <div className="web-stat__l">{s.l}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

const BRANDS = [
  ['aiko', 'AIKO'], ['ja-solar', 'JA Solar'], ['longi', 'LONGi'], ['fronius', 'Fronius'],
  ['sma', 'SMA'], ['huawei', 'Huawei'], ['top-cable', 'Top Cable'], ['prysmian', 'Prysmian'],
]

function Marquee() {
  const row = BRANDS.concat(BRANDS)
  return (
    <div className="web-marquee">
      <div className="web-marquee__label">Compatible con el equipamiento que ya usas</div>
      <div className="web-marquee__track">
        {row.map(([slug, nm], i) => (
          <span className="web-marquee__item" key={i}>
            <img className="web-marquee__logo" src={`/brand-logos/${slug}.svg`} alt={nm} />
          </span>
        ))}
      </div>
    </div>
  )
}

const FEATURES = [
  { icon: 'sliders-horizontal', t: 'Asistente de diseño', d: 'Un flujo guiado de 4 pasos con resumen en vivo: cada cambio recalcula y avisa qué quedó desactualizado.' },
  { icon: 'shield-check', t: 'Cálculos auditables', d: 'Cada resultado se puede defender: pasa el cursor y verás la fórmula y la norma aplicada (ITC-BT-40).' },
  { icon: 'package', t: 'Biblioteca de equipos', d: 'Paneles, inversores y cables con sus fichas. Añade los tuyos y reutilízalos en cada proyecto.' },
  { icon: 'file-text', t: 'Memoria y unifilar', d: 'Documento técnico y esquema unifilar listos para firmar, generados desde los datos del proyecto.' },
  { icon: 'download', t: 'Exporta a todo', d: 'CSV, Excel, PDF o al portapapeles. Tus cálculos salen en el formato que pida cada trámite.' },
  { icon: 'folder', t: 'Proyectos persistentes', d: 'Cada cliente guarda sus diseños, cálculos y memorias. Duplica una plantilla y arranca en segundos.' },
]

function Features() {
  return (
    <section className="web-section" id="features">
      <div className="web-wrap">
        <span className="web-eyebrow reveal">Funciones</span>
        <h2 className="web-h2 reveal" data-d="1" style={{ marginTop: 12 }}>Todo el tramo técnico, en una sola herramienta</h2>
        <p className="web-lead reveal" data-d="2" style={{ marginTop: 12 }}>Pensado para el instalador que legaliza: datos reales, normativa real, documentos que pasan.</p>
        <div className="web-features">
          {FEATURES.map((f, i) => (
            <div className="web-feature reveal" data-d={(i % 3) + 1} key={f.t}>
              <div className="web-feature__icon"><Icon name={f.icon} size={22} /></div>
              <h3>{f.t}</h3><p>{f.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Pbar({ p }) {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver((ents) => ents.forEach((e) => { if (e.isIntersecting) { el.classList.add('is-in'); io.disconnect() } }), { threshold: 0.5 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return <div className="web-pbar" ref={ref}><i style={{ transform: `scaleX(${p / 100})` }} /></div>
}

function Showcase() {
  const rows = [
    { nm: 'LONGi Hi-MO6', mt: '12 paneles · 2 strings', val: '6,60 kWp', p: 100 },
    { nm: 'Fronius PRIMO 5.0', mt: 'Ratio DC/AC 1,32', val: '5,0 kW', p: 76 },
    { nm: 'String Voc (−10 °C)', mt: '≤ Vmax inversor', val: '318,6 V', p: 38 },
  ]
  return (
    <section className="web-section web-showcase" id="showcase">
      <div className="web-wrap web-showcase__grid">
        <div>
          <span className="web-eyebrow reveal">El producto</span>
          <h2 className="web-h2 reveal" data-d="1" style={{ marginTop: 12 }}>Un resumen que se recalcula mientras diseñas</h2>
          <p className="web-lead reveal" data-d="2" style={{ marginTop: 12 }}>Cambia un panel y el dimensionado, los strings y la memoria se actualizan al instante — con avisos cuando algo queda fuera de norma.</p>
          <div className="web-showcase__list">
            {[
              ['activity', 'Resumen en vivo', 'Irradiancia, kWp, strings y producción siempre visibles.'],
              ['alert-triangle', 'Avisos por norma', 'Te frena antes de exceder el Vmax del inversor.'],
              ['file-check-2', 'Memoria al instante', 'El PDF y el unifilar crecen con tus datos.'],
            ].map((it, i) => (
              <div className="web-showcase__item reveal" data-d={i + 1} key={it[1]}>
                <span className="ck"><Icon name={it[0]} size={15} /></span>
                <div><strong>{it[1]}</strong><span>{it[2]}</span></div>
              </div>
            ))}
          </div>
        </div>
        <div className="web-showcase__shot reveal-scale" data-d="2">
          <div className="head"><Icon name="bar-chart-3" size={14} /> Análisis · J. García</div>
          <div className="web-showcase__rows">
            {rows.map((r) => (
              <div key={r.nm}>
                <div className="web-showcase__row">
                  <div><div className="nm">{r.nm}</div><div className="mt">{r.mt}</div></div>
                  <div className="val">{r.val}</div>
                </div>
                <Pbar p={r.p} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

const STEPS = [
  { t: 'Ubicación y consumo', d: 'Coordenadas, necesidad anual y autoconsumo. Cargamos el recurso solar de la zona.' },
  { t: 'Equipos', d: 'Elige panel e inversor de la biblioteca; filtramos por compatibilidad.' },
  { t: 'Análisis', d: 'Dimensionado automático con resumen en vivo y validación por norma.' },
  { t: 'Memoria', d: 'Genera el PDF y el esquema unifilar listos para presentar.' },
]

function How() {
  return (
    <section className="web-section" id="how" style={{ background: 'var(--cream)' }}>
      <div className="web-wrap">
        <span className="web-eyebrow reveal">Cómo funciona</span>
        <h2 className="web-h2 reveal" data-d="1" style={{ marginTop: 12 }}>Cuatro pasos, cero saltos de herramienta</h2>
        <div className="web-steps">
          {STEPS.map((s, i) => (
            <div className="web-step reveal" data-d={i + 1} key={s.t}>
              <div className="web-step__num">{String(i + 1).padStart(2, '0')}</div>
              <h4>{s.t}</h4><p>{s.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTA({ go }) {
  return (
    <section className="web-section">
      <div className="web-wrap">
        <div className="web-cta reveal-scale">
          <div className="web-cta__grid" />
          <div className="web-cta__sun" />
          <div className="web-cta__sun web-cta__sun--2" />
          <div className="web-cta__inner">
            <h2>Tu próxima memoria, lista hoy</h2>
            <p>Únete a los instaladores que dejaron de pelear con Word y CAD. Empieza gratis, sin tarjeta.</p>
            <Btn variant="secondary" size="lg" icon="arrow-right" onClick={() => go('signup')}>Crear cuenta gratis</Btn>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  const cols = [
    { h: 'Producto', items: ['Funciones', 'Precios', 'Novedades', 'Estado del servicio'] },
    { h: 'Recursos', items: ['Documentación', 'Normativa', 'Guías', 'Soporte'] },
    { h: 'Empresa', items: ['Sobre nosotros', 'Contacto', 'Privacidad', 'Términos'] },
  ]
  return (
    <footer className="web-footer">
      <div className="web-footer__grid">
        <div>
          <div className="web-footer__brand"><span className="mark"><Icon name="sun" size={15} strokeWidth={2.4} /></span>Sunalyze</div>
          <p>Diseño y legalización de instalaciones fotovoltaicas. De las coordenadas a la memoria firmable.</p>
        </div>
        {cols.map((c) => (
          <div key={c.h}>
            <h5>{c.h}</h5>
            <ul>{c.items.map((i) => <li key={i}><a href="#" onClick={(e) => e.preventDefault()}>{i}</a></li>)}</ul>
          </div>
        ))}
      </div>
      <div className="web-footer__bar">
        <span>© 2026 Sunalyze. Todos los derechos reservados.</span>
        <span>Hecho en España · Energía que se documenta sola</span>
      </div>
    </footer>
  )
}

function useReveal(deps) {
  useEffect(() => {
    const els = document.querySelectorAll('.web .reveal, .web .reveal-scale')
    const io = new IntersectionObserver((ents) => {
      ents.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target) } })
    }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' })
    els.forEach((el) => io.observe(el))
    const fallback = setTimeout(() => els.forEach((el) => el.classList.add('is-in')), 2400)
    return () => { io.disconnect(); clearTimeout(fallback) }
  }, deps)
}

export default function Landing() {
  const { navigate } = useTransition()
  const go = (key) => navigate(key === 'landing' ? '/' : key === 'login' ? '/login' : '/signup')
  useReveal([])
  return (
    <div className="web">
      <Nav go={go} />
      <Hero go={go} />
      <Stats />
      <Marquee />
      <Features />
      <Showcase />
      <How />
      <CTA go={go} />
      <Footer />
    </div>
  )
}

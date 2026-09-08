import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Icon } from '@/shared/ui'

const TAB_ORDER = ['concepto', 'criterio', 'flujo', 'tutorial']

function Html({ value, className }) {
  return <div className={className} dangerouslySetInnerHTML={{ __html: value }} />
}

const RENDERERS = {
  prose: (b) => <Html className="hb-prose" value={b.html} />,
  section: (b) => <h4 className="hb-section">{b.title}</h4>,
  cards: (b) => (
    <div className="hb-cards">
      {b.items.map((item, i) => (
        <div key={i} className="hb-card">
          {item.title && <strong>{item.title}</strong>}
          <Html value={item.body} />
        </div>
      ))}
    </div>
  ),
  flow: (b) => (
    <ol className="hb-flow">
      {b.items.map((item, i) => (
        <li key={i}>
          {item.title && <strong>{item.title}</strong>}
          <Html value={item.body} />
        </li>
      ))}
    </ol>
  ),
  steps: (b) => (
    <ol className="hb-steps">
      {b.items.map((item, i) => (
        <li key={i}>
          {item.title && <strong>{item.title} </strong>}
          <Html value={item.body} />
        </li>
      ))}
    </ol>
  ),
  tip: (b) => (
    <div className={`hb-note hb-note--${b.tone || 'info'}`}>
      <Icon name="lightbulb" size={14} />
      <div>
        {b.title && <strong>{b.title}</strong>}
        <Html value={b.body} />
      </div>
    </div>
  ),
  callout: (b) => (
    <div className={`hb-note hb-note--${b.tone || 'info'}`}>
      <Icon name="info" size={14} />
      <Html value={b.body} />
    </div>
  ),
  norm: (b) => (
    <div className="hb-norm">
      {b.code && <span className="hb-norm__code">{b.code}</span>}
      <Html value={b.body} />
    </div>
  ),
  screenshot: (b) => <Screenshot block={b} />,
}

function Screenshot({ block }) {
  const [missing, setMissing] = useState(false)
  if (missing) return null
  return (
    <figure className="hb-shot">
      <img src={`/help/${block.src}`} alt={block.alt || ''} loading="lazy" onError={() => setMissing(true)} />
      {block.caption && <figcaption><Html value={block.caption} /></figcaption>}
    </figure>
  )
}

export function ArticleView({ article, fellBack }) {
  const { t } = useTranslation('assist')
  const tabs = TAB_ORDER.filter((name) => article.tabs[name])
  const [active, setActive] = useState(tabs[0])
  const current = article.tabs[active] ? active : tabs[0]

  return (
    <article className="hb-article">
      <h3 className="hb-title">{article.title}</h3>
      {fellBack && (
        <div className="hb-note hb-note--info hb-fallback">
          <Icon name="languages" size={14} />
          <span>{t('helpFallback')}</span>
        </div>
      )}
      {tabs.length > 1 && (
        <div className="hb-tabs" role="tablist">
          {tabs.map((name) => (
            <button
              key={name}
              type="button"
              role="tab"
              aria-selected={name === current}
              className={`hb-tab${name === current ? ' hb-tab--active' : ''}`}
              onClick={() => setActive(name)}
            >
              {t(`helpTabs.${name}`)}
            </button>
          ))}
        </div>
      )}
      <div className="hb-blocks">
        {(article.tabs[current] || []).map((block, i) => {
          const render = RENDERERS[block.kind]
          return <div key={i} className="hb-block">{render ? render(block) : null}</div>
        })}
      </div>
    </article>
  )
}

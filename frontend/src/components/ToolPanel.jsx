import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'

const TOOL_ICONS = {
  wikidata_sparql: 'WD',
  icij_offshore_leaks: 'IC',
  firecrawl_search: 'FC',
  ofac_sdn: 'OF',
  gdelt: 'GD',
  opensanctions: 'OS',
  web_search: 'WS',
  wayback: 'WB',
}

const SOURCE_COLORS = {
  wikidata_sparql: 'var(--data)',
  icij_offshore_leaks: 'var(--accent)',
  firecrawl_search: 'var(--text-secondary)',
  ofac_sdn: 'var(--danger)',
  gdelt: 'var(--success)',
  opensanctions: 'var(--danger)',
  web_search: 'var(--data)',
  wayback: 'var(--text-secondary)',
}

export default function ToolPanel({ sources }) {
  const panelRef = useRef(null)

  useEffect(() => {
    if (!panelRef.current) return
    const ctx = gsap.context(() => {
      gsap.fromTo(panelRef.current,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.4, ease: 'power3.out' }
      )
    }, panelRef)
    return () => ctx.revert()
  }, [sources?.length])

  if (!sources?.length) return null

  return (
    <section className="section" ref={panelRef} style={{ paddingTop: 0 }}>
      <div className="container">
        <h2
          className="mono"
          style={{
            fontSize: '0.8rem',
            letterSpacing: '0.15em',
            color: 'var(--accent-dim)',
            marginBottom: 24,
            textTransform: 'uppercase',
          }}
        >
          {'/*'} SOURCES {'*/'}
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 48 }}>
          {sources.map((s, i) => {
            const color = SOURCE_COLORS[s.source_type] || 'var(--text-muted)'
            const url = s.url || s.source_url || null
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  padding: '12px 16px',
                  flexWrap: 'wrap',
                }}
              >
                {/* Icon badge */}
                <span
                  className="mono"
                  style={{
                    fontSize: '0.65rem',
                    color: 'var(--bg-primary)',
                    background: color === 'var(--text-muted)' ? 'var(--text-muted)' : color,
                    padding: '3px 7px',
                    fontWeight: 600,
                    flexShrink: 0,
                    marginTop: 1,
                  }}
                >
                  {TOOL_ICONS[s.source_type] || '?'}
                </span>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Title */}
                  <span
                    className="mono"
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--text-secondary)',
                      display: 'block',
                      marginBottom: url ? 6 : 0,
                    }}
                  >
                    {s.title || s.source_type}
                  </span>

                  {/* Blue source URL link */}
                  {url && (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontSize: '0.65rem',
                        fontFamily: 'var(--font-mono)',
                        color: '#3b82f6',
                        textDecoration: 'underline',
                        textDecorationColor: 'rgba(59,130,246,0.4)',
                        wordBreak: 'break-all',
                        display: 'block',
                        background: 'rgba(59,130,246,0.07)',
                        padding: '3px 6px',
                        borderLeft: '2px solid #3b82f6',
                      }}
                      title={url}
                    >
                      ↗ {url}
                    </a>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24 }}>
          <p className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            EVIDENCE-BASED INTELLIGENCE GATHERING · ALL CLAIMS LINKED TO SOURCE
          </p>
        </div>
      </div>
    </section>
  )
}

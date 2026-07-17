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

export default function ToolPanel({ sources }) {
  const panelRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(panelRef.current,
        { y: 40, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.4, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [])

  if (!sources?.length) return null

  return (
    <section className="section" ref={panelRef} style={{ paddingTop: 0 }}>
      <div className="container">
        <h2 className="mono" style={{ fontSize: '0.8rem', letterSpacing: '0.15em', color: 'var(--accent-dim)', marginBottom: 24, textTransform: 'uppercase' }}>
          {'/*'} METHODOLOGY {'*/'}
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 48 }}>
          {sources.map((s, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: 'var(--bg-surface)', border: '1px solid var(--border)',
              padding: '8px 16px',
            }}>
              <span className="mono" style={{
                fontSize: '0.65rem', color: 'var(--bg-primary)',
                background: 'var(--text-muted)', padding: '2px 6px', fontWeight: 500,
              }}>
                {TOOL_ICONS[s.source_type] || '?'}
              </span>
              <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {s.title || s.source_type}
              </span>
            </div>
          ))}
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

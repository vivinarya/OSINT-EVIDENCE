import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'
import TerminalOutput from './TerminalOutput'

export default function ReportView({ claims, contradictions, query }) {
  const sectionRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(sectionRef.current,
        { y: 60, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.2, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [])

  const terminalLines = [
    `> INVESTIGATION: ${query}`,
    `> CLAIMS: ${claims.length}`,
    `> CONTRADICTIONS: ${contradictions.length}`,
    `> SOURCES: ${new Set(claims.map(c => c.source.source_type)).size}`,
    '---',
    ...claims.map((c) => `[${c.id}] ${c.text.slice(0, 80)}...`),
    '---',
    ...(contradictions.length ? contradictions.map((c) => `! CONFLICT: ${c.id_a} <-> ${c.id_b}`) : ['NO CONTRADICTIONS DETECTED']),
  ]

  return (
    <section className="section" ref={sectionRef}>
      <div className="container">
        <h2 className="mono" style={{
          fontSize: '0.8rem', letterSpacing: '0.15em', color: 'var(--data)', marginBottom: 32, textTransform: 'uppercase',
        }}>
          {'/*'} REPORT {'*/'}
        </h2>
        <div className="mono" style={{ marginBottom: 32, color: 'var(--text-secondary)', fontSize: '0.75rem', lineHeight: 1.8 }}>
          <p>INVESTIGATION TARGET: <span style={{ color: 'var(--accent)' }}>{query}</span></p>
          <p>TIMESTAMP: <span style={{ color: 'var(--text-muted)' }}>{new Date().toISOString().replace('T', ' ').slice(0, 19)}Z</span></p>
          <p>STATUS: <span style={{ color: 'var(--success)' }}>COMPLETE</span></p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: 20 }}>
            <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Claims</span>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', color: 'var(--accent)', marginTop: 8 }}>{claims.length}</p>
          </div>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: 20 }}>
            <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Sources</span>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', color: 'var(--data)', marginTop: 8 }}>{new Set(claims.map(c => c.source.source_type)).size}</p>
          </div>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: 20 }}>
            <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Conflicts</span>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', color: contradictions.length ? 'var(--danger)' : 'var(--success)', marginTop: 8 }}>
              {contradictions.length || 0}
            </p>
          </div>
        </div>
        <TerminalOutput lines={terminalLines} title="INVESTIGATION LOG" />
      </div>
    </section>
  )
}

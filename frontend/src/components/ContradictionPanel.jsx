import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'

export default function ContradictionPanel({ contradictions, claims }) {
  const panelRef = useRef(null)
  const hasContradictions = contradictions?.length > 0

  useEffect(() => {
    if (!hasContradictions) return
    const ctx = gsap.context(() => {
      gsap.fromTo(panelRef.current,
        { y: 60, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.3, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [hasContradictions])

  if (!hasContradictions) return null

  const getClaim = (id) => claims.find((c) => c.id === id)

  return (
    <section className="section" ref={panelRef}>
      <div className="container">
        <h2 className="mono" style={{
          fontSize: '0.8rem', letterSpacing: '0.15em', color: 'var(--danger)', marginBottom: 32, textTransform: 'uppercase',
        }}>
          {'/*'} CONTRADICTIONS {'*/'}
          <span className="mono" style={{ color: 'var(--text-muted)', marginLeft: 12, fontWeight: 400, fontSize: '0.7rem' }}>
            {contradictions.length} detected
          </span>
        </h2>
        {contradictions.map((c, i) => {
          const ca = getClaim(c.id_a)
          const cb = getClaim(c.id_b)
          return (
            <div key={i} style={{
              borderLeft: '3px solid var(--danger)', padding: '20px 24px', marginBottom: 16,
              background: 'linear-gradient(135deg, var(--bg-surface) 0%, transparent 100%)',
              position: 'relative',
            }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--danger)', letterSpacing: '0.1em' }}>
                  CONFLICT
                </span>
                <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                  {c.severity}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <div style={{ padding: 12, background: 'var(--bg-elevated)' }}>
                  <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--accent)', display: 'block', marginBottom: 6 }}>
                    CLAIM A — {ca?.id}
                  </span>
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                    {ca?.text}
                  </p>
                </div>
                <div style={{ padding: 12, background: 'var(--bg-elevated)' }}>
                  <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--data)', display: 'block', marginBottom: 6 }}>
                    CLAIM B — {cb?.id}
                  </span>
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                    {cb?.text}
                  </p>
                </div>
              </div>
              {c.reason && (
                <p className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 12, fontStyle: 'italic' }}>
                  {c.reason}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

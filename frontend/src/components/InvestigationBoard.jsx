import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'
import EvidenceCard from './EvidenceCard'

const LAYOUTS = [
  { col: 1, span: 1, row: 1, rotate: -1.5 },
  { col: 2, span: 1, row: 1, rotate: 2 },
  { col: 3, span: 1, row: 1, rotate: -1 },
  { col: 1, span: 2, row: 2, rotate: 1.5 },
  { col: 3, span: 1, row: 2, rotate: -2 },
]

export default function InvestigationBoard({ claims }) {
  const boardRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const cards = boardRef.current?.querySelectorAll('.evidence-card')
      if (cards?.length) {
        gsap.fromTo(cards,
          { y: 80, opacity: 0, scale: 0.95 },
          { y: 0, opacity: 1, scale: 1, duration: 1, stagger: 0.12, ease: 'power3.out' }
        )
      }
    })
    return () => ctx.revert()
  }, [claims])

  return (
    <section className="section" ref={boardRef}>
      <div className="container">
        <h2 className="mono" style={{
          fontSize: '0.8rem', letterSpacing: '0.15em', color: 'var(--accent)', marginBottom: 32, textTransform: 'uppercase',
        }}>
          {'/*'} EVIDENCE BOARD {'*/'}
          <span style={{ color: 'var(--text-muted)', marginLeft: 12, fontWeight: 400 }}>{claims.length} items</span>
        </h2>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20,
          alignItems: 'start', perspective: 1200,
        }}>
          {claims.slice(0, 5).map((claim, i) => {
            const l = LAYOUTS[i] || LAYOUTS[i % LAYOUTS.length]
            return (
              <div
                key={claim.id}
                className="evidence-card"
                style={{
                  gridColumn: `${l.col} / span ${l.span}`,
                  transform: `rotate(${l.rotate}deg)`,
                  transition: 'transform 0.4s var(--ease-smooth)',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = 'rotate(0deg) scale(1.02)' }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = `rotate(${l.rotate}deg)` }}
              >
                <EvidenceCard claim={claim} index={i} />
              </div>
            )
          })}
        </div>
        {claims.length > 5 && (
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              +{claims.length - 5} more claims in full report
            </span>
          </div>
        )}
      </div>
    </section>
  )
}

import { useRef, useEffect } from 'react'
import { gsap, ScrollTrigger } from '../lib/gsap'
import EvidenceCard from './EvidenceCard'

export default function InvestigationBoard({ claims }) {
  const boardRef = useRef(null)

  useEffect(() => {
    if (!boardRef.current) return

    const ctx = gsap.context(() => {
      const cards = boardRef.current.querySelectorAll('.evidence-card')
      if (!cards.length) return

      // Initial entrance animation (staggered)
      gsap.fromTo(cards,
        { y: 60, opacity: 0, scale: 0.96 },
        {
          y: 0, opacity: 1, scale: 1,
          duration: 0.9, stagger: 0.1, ease: 'power3.out',
          clearProps: 'scale',
        }
      )

      // Bounded parallax scroll: cards shift in the same direction at slightly different rates
      cards.forEach((card, i) => {
        const speed = 10 + (i % 3) * 8  // bounded depth (10px, 18px, 26px)

        gsap.to(card, {
          y: -speed,
          ease: 'none',
          scrollTrigger: {
            trigger: card,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1.2,
          },
        })
      })
    }, boardRef)

    return () => ctx.revert()
  }, [claims])

  return (
    <section className="section" ref={boardRef}>
      <div className="container">
        <h2
          className="mono"
          style={{
            fontSize: '0.8rem',
            letterSpacing: '0.15em',
            color: 'var(--accent)',
            marginBottom: 32,
            textTransform: 'uppercase',
          }}
        >
          {'/*'} EVIDENCE BOARD {'*/'}
          <span style={{ color: 'var(--text-muted)', marginLeft: 12, fontWeight: 400 }}>
            {claims.length} items
          </span>
        </h2>

        {/* Parallax grid — full list, not capped at 5 */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: 24,
            alignItems: 'start',
          }}
        >
          {claims.map((claim, i) => (
            <div
              key={claim.id}
              className="evidence-card"
              style={{
                // Slight rotate for corkboard feel, straightens on hover
                transform: `rotate(${[-1.2, 1.5, -0.8, 1.8, -1.5, 1][i % 6]}deg)`,
                transition: 'transform 0.35s cubic-bezier(0.65,0,0.35,1)',
                willChange: 'transform',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'rotate(0deg) scale(1.02)'
                e.currentTarget.style.zIndex = '10'
              }}
              onMouseLeave={(e) => {
                const angles = [-1.2, 1.5, -0.8, 1.8, -1.5, 1]
                e.currentTarget.style.transform = `rotate(${angles[i % 6]}deg)`
                e.currentTarget.style.zIndex = ''
              }}
            >
              <EvidenceCard claim={claim} index={i} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

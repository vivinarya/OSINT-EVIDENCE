import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'

export default function Header() {
  const containerRef = useRef(null)
  const titleRef = useRef(null)
  const subtitleRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const chars = titleRef.current?.querySelectorAll('.char')
      if (chars?.length) {
        gsap.fromTo(chars,
          { y: 120, opacity: 0, rotateX: -45 },
          { y: 0, opacity: 1, rotateX: 0, duration: 1.2, stagger: 0.04, ease: 'power4.out', delay: 0.2 }
        )
      }
      if (subtitleRef.current) {
        gsap.fromTo(subtitleRef.current,
          { y: 40, opacity: 0 },
          { y: 0, opacity: 1, duration: 1, delay: 0.8, ease: 'power3.out' }
        )
      }
    })
    return () => ctx.revert()
  }, [])

  return (
    <header ref={containerRef} className="section" style={{ paddingBottom: 0, overflow: 'hidden' }}>
      <div className="container">
        <div ref={titleRef} style={{
          fontSize: 'clamp(3rem, 12vw, 10rem)', lineHeight: 0.85,
          marginBottom: 16, userSelect: 'none',
        }}>
          {'EVIDENCE'.split('').map((char, i) => (
            <span key={i} className="char" style={{
              display: 'inline-block',
              color: i === 0 ? 'var(--accent)' : 'var(--text-primary)',
            }}>
              {char}
            </span>
          ))}
        </div>
        <p ref={subtitleRef} className="mono" style={{
          color: 'var(--text-secondary)',
          fontSize: 'clamp(0.75rem, 1.2vw, 0.9rem)',
          letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 8,
        }}>
          OSINT INVESTIGATIVE AGENT · TRACE · VERIFY · REPORT
        </p>
        <div style={{
          width: 'clamp(60px, 15vw, 120px)', height: 2,
          background: 'var(--accent)', marginTop: 8,
        }} />
      </div>
    </header>
  )
}

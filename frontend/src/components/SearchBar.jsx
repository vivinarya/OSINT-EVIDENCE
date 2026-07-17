import { useState, useRef, useCallback, useEffect } from 'react'
import { gsap } from '../lib/gsap'

export default function SearchBar({ onInvestigate, loading }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)
  const containerRef = useRef(null)
  const lineRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(containerRef.current,
        { y: 60, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 1.2, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [])

  const handleSubmit = useCallback((e) => {
    e.preventDefault()
    const q = value.trim()
    if (q && !loading) onInvestigate(q)
  }, [value, loading, onInvestigate])

  const handleFocus = () => {
    gsap.to(lineRef.current, { scaleX: 1, duration: 0.5, ease: 'power3.out' })
  }

  const handleBlur = () => {
    if (!value) {
      gsap.to(lineRef.current, { scaleX: 0, duration: 0.4, ease: 'power3.out' })
    }
  }

  return (
    <section className="section" style={{ paddingTop: 48 }} ref={containerRef}>
      <div className="container">
        <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
          <label style={{
            display: 'block', fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12,
            letterSpacing: '0.1em',
          }}>
            {'>'}_ INVESTIGATE
          </label>
          <div style={{ position: 'relative' }}>
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onFocus={handleFocus}
              onBlur={handleBlur}
              placeholder="Entity name, person, organization..."
              disabled={loading}
              style={{
                width: '100%', background: 'transparent', border: 'none',
                borderBottom: '1px solid var(--border)', padding: '16px 0',
                fontFamily: 'var(--font-body)', fontSize: 'clamp(1.2rem, 2.5vw, 1.8rem)',
                color: 'var(--text-primary)', outline: 'none', transition: 'color 0.3s ease',
              }}
            />
            <div ref={lineRef} style={{
              position: 'absolute', bottom: 0, left: 0, width: '100%', height: 2,
              background: 'var(--accent)', transformOrigin: 'left', transform: 'scaleX(0)',
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
            <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {loading ? 'PROCESSING...' : `${value.length} characters`}
            </span>
            <button
              type="submit"
              disabled={!value.trim() || loading}
              style={{
                background: value.trim() && !loading ? 'var(--accent)' : 'var(--border)',
                color: value.trim() && !loading ? 'var(--bg-primary)' : 'var(--text-muted)',
                border: 'none', padding: '10px 32px', fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem', letterSpacing: '0.1em', textTransform: 'uppercase',
                cursor: value.trim() && !loading ? 'pointer' : 'not-allowed',
                transition: 'all 0.3s var(--ease-smooth)',
              }}
            >
              {loading ? 'SEARCHING...' : 'INVESTIGATE'}
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}

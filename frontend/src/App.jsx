import { useState, useEffect, useCallback } from 'react'
import { ReactLenis, useLenis } from 'lenis/react'
import { gsap } from './lib/gsap'
import Header from './components/Header'
import SearchBar from './components/SearchBar'
import InvestigationBoard from './components/InvestigationBoard'
import TerminalOutput from './components/TerminalOutput'
import ContradictionPanel from './components/ContradictionPanel'
import ReportView from './components/ReportView'
import ToolPanel from './components/ToolPanel'
import MagneticCursor from './components/MagneticCursor'

const API_BASE = '/api'

export default function App() {
  const [query, setQuery] = useState('')
  const [investigating, setInvestigating] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const lenis = useLenis()

  useEffect(() => {
    if (!lenis) return
    // Correct integration: stop Lenis' internal RAF and drive it via GSAP ticker
    lenis.stop()
    const update = (time) => lenis.raf(time * 1000)
    gsap.ticker.add(update)
    gsap.ticker.lagSmoothing(0)
    lenis.start()
    return () => {
      gsap.ticker.remove(update)
    }
  }, [lenis])

  const handleInvestigate = useCallback(async (q) => {
    setQuery(q)
    setInvestigating(true)
    setResults(null)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setInvestigating(false)
    }
  }, [])

  return (
    <>
      <MagneticCursor />
      <ReactLenis root options={{ lerp: 0.1, duration: 1.0, smoothWheel: true, autoRaf: false }}>
        <Header />
        <SearchBar onInvestigate={handleInvestigate} loading={investigating} />
        {investigating && (
          <section className="section">
            <div className="container">
              <p className="mono" style={{
                color: 'var(--data)', fontSize: '0.875rem',
                animation: 'pulse 1.5s ease-in-out infinite',
              }}>
                {'>'} running investigation<span className="dots"></span>
              </p>
            </div>
          </section>
        )}
        {error && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="container">
              <p className="mono" style={{ color: 'var(--danger)', fontSize: '0.8rem' }}>
                {'!'} {error}
              </p>
            </div>
          </section>
        )}
        {results && (
          <>
            <InvestigationBoard claims={results.claims} />
            <ContradictionPanel contradictions={results.contradictions} claims={results.claims} />
            <ReportView claims={results.claims} contradictions={results.contradictions} query={query} report={results.report} />
            <ToolPanel sources={results.sources} />
          </>
        )}
        {!results && !investigating && !error && (
          <footer className="section" style={{ paddingTop: 0 }}>
            <div className="container">
              <p style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.9rem' }}>
                Enter an entity, person, or organization to begin.
              </p>
            </div>
          </footer>
        )}
      </ReactLenis>
    </>
  )
}

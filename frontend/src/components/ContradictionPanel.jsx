import { useRef, useEffect } from 'react'
import { gsap } from '../lib/gsap'

const SEVERITY_COLORS = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#6b7280',
}

function ConfidenceBar({ value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
      <div style={{ flex: 1, height: 3, background: 'var(--bg-primary)', borderRadius: 2 }}>
        <div style={{
          width: `${Math.round((value || 0) * 100)}%`,
          height: '100%', background: color, borderRadius: 2,
          transition: 'width 0.6s ease',
        }} />
      </div>
      <span className="mono" style={{ fontSize: '0.58rem', color, width: 32, textAlign: 'right' }}>
        {Math.round((value || 0) * 100)}
      </span>
    </div>
  )
}

function ClaimSide({ claim, label, accentColor }) {
  if (!claim) return <div style={{ padding: 14 }}><span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Claim not found</span></div>
  const conf = claim.confidence ?? 0
  const sa   = claim.score_breakdown?.source_authority ?? 0

  return (
    <div style={{
      padding: '14px 16px',
      background: 'var(--bg-elevated)',
      borderLeft: `3px solid ${accentColor}`,
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      height: '100%',
    }}>
      {/* Side label */}
      <div style={{ display: 'flex', justify: 'space-between', alignItems: 'center', gap: 8 }}>
        <span className="mono" style={{ fontSize: '0.6rem', color: accentColor, letterSpacing: '0.1em' }}>
          {label}
        </span>
        <span className="mono" style={{ fontSize: '0.58rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          #{claim.id}
        </span>
      </div>

      {/* Claim text */}
      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: '0.85rem',
        lineHeight: 1.65,
        color: 'var(--text-primary)',
        margin: 0,
        flex: 1,
      }}>
        {claim.text}
      </p>

      {/* Confidence */}
      <div>
        <span className="mono" style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>
          CS SCORE
        </span>
        <ConfidenceBar value={conf} color={accentColor} />
      </div>

      {/* Source authority */}
      <div>
        <span className="mono" style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>
          SOURCE AUTHORITY (SA)
        </span>
        <ConfidenceBar value={sa} color={accentColor} />
      </div>

      {/* Source URL */}
      {claim.source?.url && (
        <a
          href={claim.source.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          style={{
            fontSize: '0.63rem', fontFamily: 'var(--font-mono)',
            color: '#3b82f6',
            textDecoration: 'underline',
            textDecorationColor: 'rgba(59,130,246,0.4)',
            overflow: 'hidden', textOverflow: 'ellipsis',
            whiteSpace: 'nowrap', display: 'block',
            background: 'rgba(59,130,246,0.08)',
            padding: '3px 6px',
            borderLeft: '2px solid #3b82f6',
          }}
          title={claim.source.url}
        >
          ↗ {claim.source.url}
        </a>
      )}
    </div>
  )
}

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

  // Build a lookup map: claim id → full claim object (including score_breakdown)
  const claimMap = Object.fromEntries(claims.map(c => [c.id, c]))

  return (
    <section className="section" ref={panelRef}>
      <div className="container">
        <h2 className="mono" style={{
          fontSize: '0.8rem', letterSpacing: '0.15em',
          color: '#a855f7', marginBottom: 32, textTransform: 'uppercase',
        }}>
          {'/*'} ACTIVE DISPUTES {'*/'}
          <span className="mono" style={{ color: 'var(--text-muted)', marginLeft: 12, fontWeight: 400, fontSize: '0.7rem' }}>
            {contradictions.length} conflict{contradictions.length !== 1 ? 's' : ''} detected
          </span>
        </h2>

        {contradictions.map((c, i) => {
          const ca = claimMap[c.id_a]
          const cb = claimMap[c.id_b]
          const sevColor = SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.LOW

          return (
            <div key={i} style={{
              marginBottom: 28,
              background: 'var(--bg-surface)',
              border: `1px solid ${sevColor}`,
              position: 'relative',
              overflow: 'hidden',
            }}>
              {/* Dispute header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '9px 16px',
                background: `${sevColor}18`,
                borderBottom: `1px solid ${sevColor}`,
                flexWrap: 'wrap',
                gap: 8,
              }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <span className="mono" style={{ fontSize: '0.62rem', color: sevColor, letterSpacing: '0.1em', fontWeight: 700 }}>
                    ⚔ ACTIVE DISPUTE #{i + 1}
                  </span>
                  <span className="mono" style={{
                    fontSize: '0.58rem', color: sevColor,
                    padding: '2px 8px', border: `1px solid ${sevColor}`,
                  }}>
                    {c.severity} SEVERITY
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <span className="mono" style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>
                    {c.id_a}
                  </span>
                  <span style={{ color: sevColor }}>⟷</span>
                  <span className="mono" style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>
                    {c.id_b}
                  </span>
                </div>
              </div>

              {/* Dual-timeline comparison */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto 1fr',
                alignItems: 'stretch',
              }}>
                <ClaimSide claim={ca} label={`CLAIM A — ${c.id_a}`} accentColor="#06b6d4" />

                {/* VS divider */}
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  padding: '0 12px', background: 'var(--bg-primary)',
                  borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)',
                }}>
                  <span className="mono" style={{ fontSize: '0.7rem', color: sevColor, fontWeight: 700 }}>VS</span>
                </div>

                <ClaimSide claim={cb} label={`CLAIM B — ${c.id_b}`} accentColor="#f59e0b" />
              </div>

              {/* Reason / resolution notes */}
              {c.reason && (
                <div style={{
                  padding: '10px 16px',
                  borderTop: '1px solid var(--border)',
                  background: 'var(--bg-elevated)',
                }}>
                  <p className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', margin: 0, fontStyle: 'italic' }}>
                    ↳ {c.reason}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

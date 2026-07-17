import { useRef, useEffect, useState } from 'react'
import { gsap } from '../lib/gsap'

// Renders a single line of the report with proper inline markdown styling
function ReportLine({ line }) {
  if (!line.trim()) return <div style={{ height: 8 }} />

  // Section headers: ## or #
  if (line.startsWith('## ')) {
    return (
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: '1rem',
        letterSpacing: '0.05em',
        color: 'var(--accent)',
        marginTop: 28,
        marginBottom: 10,
        paddingBottom: 6,
        borderBottom: '1px solid var(--border)',
        textTransform: 'uppercase',
      }}>
        {line.replace(/^## /, '')}
      </h3>
    )
  }
  if (line.startsWith('# ')) {
    return (
      <h2 style={{
        fontFamily: 'var(--font-display)',
        fontSize: '1.25rem',
        letterSpacing: '0.03em',
        color: 'var(--text-primary)',
        marginBottom: 16,
      }}>
        {line.replace(/^# /, '')}
      </h2>
    )
  }
  if (line.startsWith('### ')) {
    return (
      <h4 style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        letterSpacing: '0.1em',
        color: 'var(--data)',
        marginTop: 16,
        marginBottom: 6,
        textTransform: 'uppercase',
      }}>
        {line.replace(/^### /, '')}
      </h4>
    )
  }

  // List items: - or *
  if (line.match(/^[-*] /)) {
    const content = line.replace(/^[-*] /, '')
    return (
      <div style={{ display: 'flex', gap: 10, marginBottom: 6, paddingLeft: 4 }}>
        <span style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }}>›</span>
        <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-primary)' }}>
          {renderInline(content)}
        </span>
      </div>
    )
  }

  // Indented sub-items (2+ spaces or tab)
  if (line.match(/^\s{2,}/)) {
    return (
      <div style={{ paddingLeft: 20, marginBottom: 4 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {renderInline(line.trim())}
        </span>
      </div>
    )
  }

  // Separator
  if (line === '---') {
    return <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '16px 0' }} />
  }

  // Default paragraph
  return (
    <p style={{
      fontFamily: 'var(--font-body)',
      fontSize: '0.9rem',
      lineHeight: 1.7,
      color: 'var(--text-secondary)',
      marginBottom: 6,
    }}>
      {renderInline(line)}
    </p>
  )
}

// Render inline markdown: **bold**, *italic*, bare URLs, [source] refs
function renderInline(text) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|\[c_\d{3}\]|https?:\/\/[^\s,)"'\]]+)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return <em key={i} style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>{part.slice(1, -1)}</em>
    }
    if (part.match(/^\[c_\d{3}\]$/)) {
      return (
        <code key={i} style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.65rem',
          background: 'rgba(245,158,11,0.15)',
          color: 'var(--accent)',
          padding: '1px 5px',
          borderRadius: 3,
          marginLeft: 3,
        }}>
          {part}
        </code>
      )
    }
    if (/^https?:\/\//.test(part)) {
      return (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer"
          style={{
            color: '#3b82f6',
            textDecoration: 'underline',
            textDecorationColor: 'rgba(59,130,246,0.4)',
            wordBreak: 'break-all',
            fontSize: '0.78rem',
          }}
        >
          ↗ {part}
        </a>
      )
    }
    return part
  })
}

// Mini stat pill
function StatPill({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1px solid ${color || 'var(--border)'}`,
      padding: '14px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
    }}>
      <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
        {label}
      </span>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: color || 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </span>
    </div>
  )
}

export default function ReportView({ claims, contradictions, query, report }) {
  const sectionRef = useRef(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(sectionRef.current,
        { y: 60, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, delay: 0.2, ease: 'power3.out' }
      )
    })
    return () => ctx.revert()
  }, [])

  const highConf = claims.filter(c => c.confidence >= 0.7).length
  const sourceCount = new Set(claims.map(c => c.source?.source_url)).size

  // Parse report text into lines — guard against non-string values from the API
  const reportText = report && typeof report === 'string' ? report
    : report && typeof report === 'object' ? JSON.stringify(report, null, 2)
    : ''
  const reportLines = reportText ? reportText.split('\n') : []

  return (
    <section className="section" ref={sectionRef}>
      <div className="container">

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <h2 className="mono" style={{
            fontSize: '0.8rem', letterSpacing: '0.15em',
            color: 'var(--data)', marginBottom: 4, textTransform: 'uppercase',
          }}>
            {'/*'} INVESTIGATION REPORT {'*/'}
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            {query}
          </p>
        </div>

        {/* Stats grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 32 }}>
          <StatPill label="Total Claims" value={claims.length} color="var(--accent)" />
          <StatPill label="Unique Sources" value={sourceCount} color="var(--data)" />
          <StatPill label="High Confidence" value={highConf} color="var(--success)" />
          <StatPill
            label="Conflicts"
            value={contradictions.length || 0}
            color={contradictions.length ? 'var(--danger)' : 'var(--success)'}
          />
          <StatPill
            label="Timestamp"
            value={new Date().toISOString().slice(11, 19) + 'Z'}
            color="var(--text-muted)"
          />
        </div>

        {/* Rendered report body */}
        {reportLines.length > 0 ? (
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 0,
            overflow: 'hidden',
          }}>
            {/* Report header bar */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '10px 20px',
              background: 'var(--bg-elevated)',
              borderBottom: '1px solid var(--border)',
            }}>
              <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--accent)', letterSpacing: '0.1em' }}>
                FULL REPORT — {reportLines.length} LINES
              </span>
              <button
                onClick={() => setExpanded(!expanded)}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.6rem',
                  letterSpacing: '0.1em',
                  color: 'var(--text-muted)',
                  background: 'transparent',
                  border: '1px solid var(--border)',
                  padding: '3px 10px',
                  cursor: 'pointer',
                  textTransform: 'uppercase',
                }}
              >
                {expanded ? '▲ COLLAPSE' : '▼ EXPAND'}
              </button>
            </div>

            {/* Report content */}
            <div style={{
              padding: '20px 24px',
              maxHeight: expanded ? 'none' : 420,
              overflow: 'hidden',
              position: 'relative',
            }}>
              {reportLines.map((line, i) => (
                <ReportLine key={i} line={line} />
              ))}

              {/* Fade gradient when collapsed */}
              {!expanded && (
                <div style={{
                  position: 'absolute',
                  bottom: 0, left: 0, right: 0,
                  height: 80,
                  background: 'linear-gradient(to bottom, transparent, var(--bg-surface))',
                  pointerEvents: 'none',
                }} />
              )}
            </div>
          </div>
        ) : (
          /* Fallback: no report text, show structured summary */
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: 24 }}>
            <div className="mono" style={{ marginBottom: 20, color: 'var(--text-secondary)', fontSize: '0.75rem', lineHeight: 1.8 }}>
              <p>INVESTIGATION TARGET: <span style={{ color: 'var(--accent)' }}>{query}</span></p>
              <p>TIMESTAMP: <span style={{ color: 'var(--text-muted)' }}>{new Date().toISOString().replace('T', ' ').slice(0, 19)}Z</span></p>
              <p>STATUS: <span style={{ color: 'var(--success)' }}>COMPLETE</span></p>
            </div>
            {claims.slice(0, 10).map(c => (
              <div key={c.id} style={{ borderLeft: '2px solid var(--border)', paddingLeft: 14, marginBottom: 12 }}>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: 4 }}>
                  {c.text}
                </p>
                <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                  {c.id} · confidence {(c.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

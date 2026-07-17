import { useState } from 'react'
import SourceBadge from './SourceBadge'

const STATE_CONFIG = {
  VERIFIED_FACT: {
    label: 'VERIFIED FACT',
    color: '#88b67f',
    bg: 'rgba(136,182,127,0.08)',
    border: '#88b67f',
    desc: 'Corroborated by multiple independent sources',
  },
  BREAKING_CLAIM: {
    label: 'BREAKING CLAIM',
    color: '#c58c2c',
    bg: 'rgba(197,140,44,0.08)',
    border: '#c58c2c',
    desc: 'Sole or unverified source - requires corroboration',
  },
  ACTIVE_DISPUTE: {
    label: 'ACTIVE DISPUTE',
    color: '#9b6b5a',
    bg: 'rgba(155,107,90,0.10)',
    border: '#9b6b5a',
    desc: 'Contradictory evidence found - competing claims exist',
  },
  DEBUNKED: {
    label: 'DEBUNKED',
    color: '#b35d50',
    bg: 'rgba(179,93,80,0.10)',
    border: '#b35d50',
    desc: 'High-authority source actively contradicts this claim',
  },
  UNSCORED: {
    label: 'UNSCORED',
    color: '#6b7280',
    bg: 'rgba(107,114,128,0.10)',
    border: '#6b7280',
    desc: 'Scoring pipeline has not yet run',
  },
}

function renderMarkdown(text) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|https?:\/\/[^\s,)"']+)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return <em key={i} style={{ color: 'var(--text-secondary)' }}>{part.slice(1, -1)}</em>
    }
    if (/^https?:\/\//.test(part)) {
      return (
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          style={{ color: '#6ea0ff', textDecoration: 'underline', wordBreak: 'break-all' }}
        >
          {part}
        </a>
      )
    }
    return part
  })
}

function ScoreBreakdownBar({ breakdown, cs }) {
  if (!breakdown) return null

  const rows = [
    {
      label: 'Source authority',
      short: 'SA',
      value: breakdown.source_authority ?? 0,
      tone: '#b8b2a7',
    },
    {
      label: 'Temporal factor',
      short: 'TF',
      value: breakdown.temporal_factor ?? 0,
      tone: '#9b9488',
    },
    {
      label: 'Corroboration',
      short: 'CC',
      value: breakdown.corroboration_score ?? 0,
      tone: '#878075',
    },
    {
      label: 'Independence',
      short: 'NI',
      value: breakdown.network_independence ?? 0,
      tone: '#736d63',
    },
  ]

  return (
    <div style={{ marginTop: 10 }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: 12,
      }}>
        <div>
          <p className="mono" style={{
            fontSize: '0.54rem',
            color: 'var(--text-muted)',
            letterSpacing: '0.12em',
            margin: 0,
            textTransform: 'uppercase',
          }}>
            Confidence score
          </p>
          <p className="mono" style={{
            fontSize: '0.54rem',
            color: 'var(--text-muted)',
            letterSpacing: '0.06em',
            margin: '3px 0 0',
          }}>
            SA x TF x CC x NI
          </p>
        </div>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '1.15rem',
          lineHeight: 1,
          color: 'var(--text-primary)',
        }}>
          {typeof cs === 'number' ? cs.toFixed(1) : '?'}
          <span className="mono" style={{
            fontSize: '0.62rem',
            color: 'var(--text-muted)',
            marginLeft: 6,
            letterSpacing: '0.08em',
          }}>
            / 100
          </span>
        </span>
      </div>

      {rows.map(row => (
        <div key={row.short} title={row.label} style={{ marginBottom: 9 }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '28px 1fr 34px',
            alignItems: 'center',
            gap: 10,
            marginBottom: 4,
          }}>
            <span className="mono" style={{
              fontSize: '0.55rem',
              color: row.tone,
              letterSpacing: '0.08em',
            }}>
              {row.short}
            </span>
            <div style={{
              height: 2,
              background: 'rgba(255,255,255,0.08)',
              position: 'relative',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${Math.max(3, row.value * 100)}%`,
                height: '100%',
                background: row.tone,
                boxShadow: `0 0 10px ${row.tone}22`,
                transition: 'width 0.8s cubic-bezier(0.65,0,0.35,1)',
              }} />
            </div>
            <span className="mono" style={{
              fontSize: '0.55rem',
              color: 'var(--text-muted)',
              textAlign: 'right',
            }}>
              {(row.value * 100).toFixed(0)}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

function ClaimTypeBadge({ claimType, decayLambda }) {
  if (!claimType) return null

  const isStatic = claimType === 'static'
  const label = isStatic
    ? 'STATIC'
    : claimType === 'dynamic_high'
      ? 'HIGH DECAY'
      : claimType === 'dynamic_medium'
        ? 'MED DECAY'
        : 'LOW DECAY'
  const color = isStatic
    ? '#767676'
    : claimType === 'dynamic_high'
      ? '#a8614f'
      : claimType === 'dynamic_medium'
        ? '#b8873a'
        : '#728b63'

  return (
    <span
      className="mono"
      style={{
        fontSize: '0.55rem',
        color,
        padding: '2px 6px',
        border: `1px solid ${color}`,
        letterSpacing: '0.05em',
      }}
      title={isStatic ? 'Historical fact - no decay' : `lambda=${decayLambda} decay rate`}
    >
      {label}
    </span>
  )
}

export default function EvidenceCard({ claim }) {
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [showNotes, setShowNotes] = useState(false)

  const state = claim.confidence_state || 'UNSCORED'
  const stateConf = STATE_CONFIG[state] || STATE_CONFIG.UNSCORED
  const corrCount = claim.corroborating_claim_ids?.length || 0
  const contCount = claim.contradicting_claim_ids?.length || 0
  const cs = claim.confidence_raw ?? (claim.confidence * 100)

  const handleExplain = async (e) => {
    e.stopPropagation()
    if (explanation) {
      setExplanation(null)
      return
    }
    setExplaining(true)
    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_id: claim.id }),
      })
      if (!res.ok) throw new Error('Explain failed')
      const data = await res.json()
      setExplanation(data.explanation || 'No explanation available')
    } catch {
      setExplanation('Failed to load explanation.')
    } finally {
      setExplaining(false)
    }
  }

  return (
    <div style={{
      background: 'linear-gradient(180deg, rgba(24,24,28,0.98) 0%, rgba(18,18,21,1) 100%)',
      border: `1px solid ${stateConf.border}`,
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden',
      boxShadow: '0 20px 40px rgba(0,0,0,0.18)',
    }}>
      <div style={{
        background: stateConf.bg,
        borderBottom: `1px solid ${stateConf.border}`,
        padding: '8px 14px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 6,
      }}>
        <span className="mono" style={{
          fontSize: '0.62rem',
          color: stateConf.color,
          letterSpacing: '0.12em',
          fontWeight: 700,
        }}>
          {stateConf.label}
        </span>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <ClaimTypeBadge claimType={claim.claim_type} decayLambda={claim.decay_lambda} />
          {claim.echo_chamber && (
            <span className="mono" style={{ fontSize: '0.55rem', color: '#a87140', padding: '2px 6px', border: '1px solid #a87140' }}>
              ECHO CHAMBER
            </span>
          )}
          {corrCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.58rem', color: '#6f9a67', padding: '2px 6px', border: '1px solid #6f9a67' }}>
              +{corrCount} corr
            </span>
          )}
          {contCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.58rem', color: '#a8614f', padding: '2px 6px', border: '1px solid #a8614f' }}>
              !{contCount} contr
            </span>
          )}
          <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>#{claim.id}</span>
        </div>
      </div>

      <div style={{ padding: '16px 16px 12px' }}>
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'clamp(0.92rem, 1.2vw, 1.02rem)',
          lineHeight: 1.72,
          color: 'var(--text-primary)',
          margin: 0,
        }}>
          {renderMarkdown(claim.text)}
        </p>
      </div>

      <div style={{ padding: '0 16px 14px' }}>
        <ScoreBreakdownBar breakdown={claim.score_breakdown} cs={cs} />
      </div>

      <div style={{ padding: '0 16px 12px' }}>
        <SourceBadge source={claim.source} />
      </div>

      <div style={{
        padding: '8px 16px 12px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        <p className="mono" style={{
          fontSize: '0.6rem',
          color: 'var(--text-secondary)',
          fontStyle: 'italic',
          margin: 0,
        }}>
          {stateConf.desc}
        </p>
      </div>

      <div style={{
        display: 'flex',
        borderTop: '1px solid var(--border)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <button className="card-action-btn" onClick={handleExplain} style={{
          borderRight: '1px solid var(--border)',
        }}>
          {explaining ? '...' : explanation ? 'COLLAPSE' : 'EXPLAIN'}
        </button>
        {claim.scoring_notes?.length > 0 && (
          <button className="card-action-btn" onClick={() => setShowNotes(n => !n)}>
            {showNotes ? 'HIDE TRACE' : 'AGENT TRACE'}
          </button>
        )}
      </div>

      {explanation && (
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-elevated)',
          borderLeft: `3px solid ${stateConf.border}`,
          fontSize: '0.78rem',
          lineHeight: 1.7,
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)',
          whiteSpace: 'pre-wrap',
        }}>
          {explanation}
        </div>
      )}

      {showNotes && claim.scoring_notes?.length > 0 && (
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-primary)',
        }}>
          <p className="mono" style={{
            fontSize: '0.58rem',
            color: '#8b8172',
            marginBottom: 8,
            letterSpacing: '0.08em',
          }}>
            MULTI-AGENT SCORING TRACE
          </p>
          {claim.scoring_notes.map((note, i) => (
            <p key={i} className="mono" style={{
              fontSize: '0.62rem',
              lineHeight: 1.6,
              color: note.startsWith('[FORMULA]') ? '#b8873a'
                : note.startsWith('[STATE]') ? '#88b67f'
                : note.startsWith('[ADVERSARIAL]') ? '#a8614f'
                : 'var(--text-muted)',
              marginBottom: 4,
            }}>
              {note}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

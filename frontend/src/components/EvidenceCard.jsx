import { useState } from 'react'
import SourceBadge from './SourceBadge'

// ── Logic state config ───────────────────────────────────────────────────────
const STATE_CONFIG = {
  VERIFIED_FACT: {
    label: '✓ VERIFIED FACT',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.10)',
    border: '#22c55e',
    desc: 'Corroborated by multiple independent sources',
  },
  BREAKING_CLAIM: {
    label: '⚡ BREAKING CLAIM',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.10)',
    border: '#f59e0b',
    desc: 'Sole or unverified source — requires corroboration',
  },
  ACTIVE_DISPUTE: {
    label: '⚠ ACTIVE DISPUTE',
    color: '#a855f7',
    bg: 'rgba(168,85,247,0.10)',
    border: '#a855f7',
    desc: 'Contradictory evidence found — competing claims exist',
  },
  DEBUNKED: {
    label: '✗ DEBUNKED',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.10)',
    border: '#ef4444',
    desc: 'High-authority source actively contradicts this claim',
  },
  UNSCORED: {
    label: '○ UNSCORED',
    color: '#6b7280',
    bg: 'rgba(107,114,128,0.10)',
    border: '#6b7280',
    desc: 'Scoring pipeline has not yet run',
  },
}

// Simple inline markdown renderer
function renderMarkdown(text) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|https?:\/\/[^\s,)"']+)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2)
      return <em key={i} style={{ color: 'var(--text-secondary)' }}>{part.slice(1, -1)}</em>
    if (/^https?:\/\//.test(part))
      return <a key={i} href={part} target="_blank" rel="noopener noreferrer"
        onClick={e => e.stopPropagation()}
        style={{ color: '#3b82f6', textDecoration: 'underline', wordBreak: 'break-all' }}>{part}</a>
    return part
  })
}

// Score breakdown bar — shows SA, TF, CC, NI as stacked segments
function ScoreBreakdownBar({ breakdown, cs }) {
  if (!breakdown) return null
  const { source_authority: sa, temporal_factor: tf, corroboration_score: cc, network_independence: ni } = breakdown

  const bars = [
    { label: 'SA', value: sa, color: '#06b6d4', title: `Source Authority: ${(sa * 100).toFixed(0)}%` },
    { label: 'TF', value: tf, color: '#f59e0b', title: `Temporal Factor: ${(tf * 100).toFixed(0)}%` },
    { label: 'CC', value: cc, color: '#22c55e', title: `Corroboration: ${(cc * 100).toFixed(0)}%` },
    { label: 'NI', value: ni, color: '#a855f7', title: `Net. Independence: ${(ni * 100).toFixed(0)}%` },
  ]

  return (
    <div style={{ marginTop: 10 }}>
      {/* CS score display */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
          CS = (SA×TF)×(CC×NI)×100
        </span>
        <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--accent)', fontWeight: 600 }}>
          {typeof cs === 'number' ? cs.toFixed(1) : '?'} / 100
        </span>
      </div>
      {/* Component bars */}
      {bars.map(bar => (
        <div key={bar.label} title={bar.title} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span className="mono" style={{ fontSize: '0.55rem', color: bar.color, width: 18, flexShrink: 0 }}>{bar.label}</span>
          <div style={{ flex: 1, height: 4, background: 'var(--bg-primary)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{
              width: `${Math.max(2, bar.value * 100)}%`,
              height: '100%',
              background: bar.color,
              borderRadius: 2,
              transition: 'width 0.8s cubic-bezier(0.65,0,0.35,1)',
            }} />
          </div>
          <span className="mono" style={{ fontSize: '0.55rem', color: 'var(--text-muted)', width: 28, textAlign: 'right' }}>
            {(bar.value * 100).toFixed(0)}%
          </span>
        </div>
      ))}
    </div>
  )
}

// Claim type badge
function ClaimTypeBadge({ claimType, decayLambda }) {
  if (!claimType) return null
  const isStatic = claimType === 'static'
  const label = isStatic ? '⏸ STATIC' : claimType === 'dynamic_high' ? '🔴 HIGH DECAY' : claimType === 'dynamic_medium' ? '🟡 MED DECAY' : '🟢 LOW DECAY'
  const color = isStatic ? '#6b7280' : claimType === 'dynamic_high' ? '#ef4444' : claimType === 'dynamic_medium' ? '#f59e0b' : '#22c55e'

  return (
    <span className="mono" style={{
      fontSize: '0.55rem', color, padding: '2px 6px',
      border: `1px solid ${color}`, letterSpacing: '0.05em',
    }} title={isStatic ? 'Historical fact — no decay' : `λ=${decayLambda} decay rate`}>
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
    if (explanation) { setExplanation(null); return }
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
      background: 'var(--bg-surface)',
      border: `1px solid ${stateConf.border}`,
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* State banner */}
      <div style={{
        background: stateConf.bg,
        borderBottom: `1px solid ${stateConf.border}`,
        padding: '7px 14px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 6,
      }}>
        <span className="mono" style={{ fontSize: '0.62rem', color: stateConf.color, letterSpacing: '0.08em', fontWeight: 700 }}>
          {stateConf.label}
        </span>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          <ClaimTypeBadge claimType={claim.claim_type} decayLambda={claim.decay_lambda} />
          {claim.echo_chamber && (
            <span className="mono" style={{ fontSize: '0.55rem', color: '#f97316', padding: '2px 6px', border: '1px solid #f97316' }}>
              ⟳ ECHO CHAMBER
            </span>
          )}
          {corrCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.58rem', color: '#22c55e', padding: '2px 6px', border: '1px solid #22c55e' }}>
              +{corrCount} corr
            </span>
          )}
          {contCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.58rem', color: '#ef4444', padding: '2px 6px', border: '1px solid #ef4444' }}>
              !{contCount} contr
            </span>
          )}
          <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>#{claim.id}</span>
        </div>
      </div>

      {/* Claim text */}
      <div style={{ padding: '14px 16px 10px' }}>
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'clamp(0.88rem, 1.2vw, 1rem)',
          lineHeight: 1.7,
          color: 'var(--text-primary)',
          margin: 0,
        }}>
          {renderMarkdown(claim.text)}
        </p>
      </div>

      {/* Score breakdown */}
      <div style={{ padding: '0 16px 12px' }}>
        <ScoreBreakdownBar breakdown={claim.score_breakdown} cs={cs} />
      </div>

      {/* Source info */}
      <div style={{ padding: '0 16px 12px' }}>
        <SourceBadge source={claim.source} />
      </div>

      {/* State description */}
      <div style={{
        padding: '6px 16px 10px',
        borderTop: '1px solid var(--border)',
      }}>
        <p className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
          {stateConf.desc}
        </p>
      </div>

      {/* Action row */}
      <div style={{
        display: 'flex',
        borderTop: '1px solid var(--border)',
        background: 'var(--bg-elevated)',
      }}>
        <button onClick={handleExplain} style={{
          flex: 1, padding: '7px 0', background: 'transparent', border: 'none',
          borderRight: '1px solid var(--border)', cursor: 'pointer',
          fontFamily: 'var(--font-mono)', fontSize: '0.58rem', letterSpacing: '0.06em',
          color: 'var(--text-muted)', textTransform: 'uppercase',
        }}>
          {explaining ? '…' : explanation ? '▲ COLLAPSE' : '▼ EXPLAIN'}
        </button>
        {claim.scoring_notes?.length > 0 && (
          <button onClick={() => setShowNotes(n => !n)} style={{
            flex: 1, padding: '7px 0', background: 'transparent', border: 'none',
            cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '0.58rem',
            letterSpacing: '0.06em', color: 'var(--text-muted)', textTransform: 'uppercase',
          }}>
            {showNotes ? '▲ HIDE TRACE' : '▼ AGENT TRACE'}
          </button>
        )}
      </div>

      {/* Explanation panel */}
      {explanation && (
        <div style={{
          padding: '12px 16px', borderTop: '1px solid var(--border)',
          background: 'var(--bg-elevated)', borderLeft: `3px solid ${stateConf.border}`,
          fontSize: '0.78rem', lineHeight: 1.7, fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)', whiteSpace: 'pre-wrap',
        }}>
          {explanation}
        </div>
      )}

      {/* Agent trace panel */}
      {showNotes && claim.scoring_notes?.length > 0 && (
        <div style={{
          padding: '12px 16px', borderTop: '1px solid var(--border)',
          background: 'var(--bg-primary)',
        }}>
          <p className="mono" style={{ fontSize: '0.58rem', color: '#a855f7', marginBottom: 8, letterSpacing: '0.08em' }}>
            ▶ MULTI-AGENT SCORING TRACE
          </p>
          {claim.scoring_notes.map((note, i) => (
            <p key={i} className="mono" style={{
              fontSize: '0.62rem', lineHeight: 1.6,
              color: note.startsWith('[FORMULA]') ? '#f59e0b'
                : note.startsWith('[STATE]') ? '#22c55e'
                : note.startsWith('[ADVERSARIAL]') ? '#ef4444'
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

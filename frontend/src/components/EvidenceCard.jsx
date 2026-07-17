import { useState } from 'react'
import SourceBadge from './SourceBadge'

const CONFIDENCE_COLORS = {
  high: 'var(--success)',
  medium: 'var(--accent)',
  low: 'var(--text-muted)',
}

function getConfidenceLevel(score) {
  if (score >= 0.7) return 'high'
  if (score >= 0.4) return 'medium'
  return 'low'
}

export default function EvidenceCard({ claim }) {
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const level = getConfidenceLevel(claim.confidence)
  const color = CONFIDENCE_COLORS[level]
  const corrCount = claim.corroborating_claim_ids?.length || 0
  const contCount = claim.contradicting_claim_ids?.length || 0

  const handleExplain = async () => {
    if (explanation) {
      setExplaining(false)
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
      setExplanation('Failed to load explanation. Run an investigation first.')
    } finally {
      setExplaining(false)
    }
  }

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: `1px solid ${corrCount >= 1 ? 'var(--success)' : contCount >= 1 ? 'var(--danger)' : 'var(--border)'}`,
      padding: 20,
      position: 'relative',
      overflow: 'hidden',
      cursor: 'pointer',
    }} onClick={handleExplain}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 12,
        gap: 8,
        flexWrap: 'wrap',
      }}>
        <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
          #{claim.id}
        </span>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {corrCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--success)', padding: '2px 6px', border: '1px solid var(--success)' }}>
              +{corrCount}
            </span>
          )}
          {contCount >= 1 && (
            <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--danger)', padding: '2px 6px', border: '1px solid var(--danger)' }}>
              !{contCount}
            </span>
          )}
          <span className="mono" style={{ fontSize: '0.65rem', color, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block' }} />
            {level.toUpperCase()}
          </span>
        </div>
      </div>
      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: 'clamp(0.85rem, 1.2vw, 1rem)',
        lineHeight: 1.6,
        color: 'var(--text-primary)',
        marginBottom: 16,
      }}>
        {claim.text}
      </p>
      <SourceBadge source={claim.source} />
      {explaining && (
        <p className="mono" style={{ fontSize: '0.7rem', color: 'var(--data)', marginTop: 8 }}>Loading explanation...</p>
      )}
      {explanation && (
        <div style={{
          marginTop: 12,
          padding: 12,
          background: 'var(--bg-elevated)',
          borderLeft: '3px solid var(--accent)',
          fontSize: '0.75rem',
          lineHeight: 1.7,
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)',
          whiteSpace: 'pre-wrap',
        }}>
          {explanation}
        </div>
      )}
      <div style={{
        position: 'absolute',
        bottom: 0,
        right: 0,
        width: 60,
        height: 60,
        borderLeft: '1px solid var(--border)',
        borderTop: '1px solid var(--border)',
        background: 'var(--bg-elevated)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
          {(claim.confidence * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}

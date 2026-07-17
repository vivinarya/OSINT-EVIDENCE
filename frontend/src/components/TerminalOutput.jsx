import { useRef, useState, useEffect } from 'react'

const TYPING_SPEED = 15

export default function TerminalOutput({ lines, title }) {
  const [visible, setVisible] = useState(0)
  const containerRef = useRef(null)

  useEffect(() => {
    setVisible(0)
    if (!lines?.length) return
    const interval = setInterval(() => {
      setVisible((v) => {
        if (v >= lines.length) { clearInterval(interval); return v }
        return v + 1
      })
    }, TYPING_SPEED * 30)
    return () => clearInterval(interval)
  }, [lines])

  return (
    <div
      ref={containerRef}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        lineHeight: 1.7,
        overflow: 'hidden',
      }}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-elevated)',
      }}>
        <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--data)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {title || 'TERMINAL'}
        </span>
        <span className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
          {visible}/{lines?.length || 0}
        </span>
      </div>
      <div style={{ padding: 16, minHeight: 100 }}>
        {lines?.slice(0, visible).map((line, i) => (
          <div key={i} style={{ color: line.startsWith('>') ? 'var(--data)' : 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
            <span style={{ color: 'var(--text-muted)', marginRight: 8 }}>{String(i + 1).padStart(2, '0')}</span>
            {line}
          </div>
        ))}
        {visible < (lines?.length || 0) && (
          <span style={{ color: 'var(--data)', animation: 'blink 1s step-end infinite' }}>▊</span>
        )}
      </div>
      <style>{`@keyframes blink { 50% { opacity: 0 } }`}</style>
    </div>
  )
}

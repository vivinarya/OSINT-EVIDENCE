const SOURCE_LABELS = {
  wikidata_sparql: 'WIKIDATA',
  icij_offshore_leaks: 'ICIJ',
  firecrawl_search: 'WEB',
  ofac_sdn: 'OFAC',
  gdelt: 'GDELT',
  opensanctions: 'SANCTIONS',
  web_search: 'WEB',
  wayback: 'ARCHIVE',
}

const SOURCE_COLORS = {
  wikidata_sparql: 'var(--data)',
  icij_offshore_leaks: 'var(--accent)',
  firecrawl_search: 'var(--text-secondary)',
  ofac_sdn: 'var(--danger)',
  gdelt: 'var(--success)',
  opensanctions: 'var(--danger)',
  web_search: 'var(--data)',
  wayback: 'var(--text-secondary)',
}

export default function SourceBadge({ source }) {
  if (!source) return null

  const label = SOURCE_LABELS[source.source_type] || (source.source_type || '').toUpperCase()
  const color = SOURCE_COLORS[source.source_type] || 'var(--text-muted)'

  // Extract the actual URL — could be source.url, source.source_url, or source.retrieval_tool if it's a URL
  const url = source.url || source.source_url || null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
      {/* Source type badge + retrieval tool row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span
          className="mono"
          style={{
            fontSize: '0.6rem',
            letterSpacing: '0.1em',
            padding: '2px 8px',
            border: `1px solid ${color}`,
            color: color,
            background: 'transparent',
            flexShrink: 0,
          }}
        >
          {label}
        </span>
        {source.retrieval_tool && (
          <span
            className="mono"
            style={{
              fontSize: '0.6rem',
              color: 'var(--text-muted)',
              padding: '2px 6px',
              border: '1px solid var(--border)',
            }}
          >
            {source.retrieval_tool}
          </span>
        )}
      </div>

      {/* Source URL as blue clickable link */}
      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          style={{
            fontSize: '0.65rem',
            fontFamily: 'var(--font-mono)',
            color: '#3b82f6',
            textDecoration: 'underline',
            textDecorationColor: 'rgba(59,130,246,0.4)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            maxWidth: '100%',
            display: 'block',
            background: 'rgba(59,130,246,0.08)',
            padding: '3px 6px',
            borderLeft: '2px solid #3b82f6',
            transition: 'background 0.2s ease, color 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(59,130,246,0.18)'
            e.currentTarget.style.color = '#60a5fa'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(59,130,246,0.08)'
            e.currentTarget.style.color = '#3b82f6'
          }}
          title={url}
        >
          ↗ {url}
        </a>
      )}
    </div>
  )
}

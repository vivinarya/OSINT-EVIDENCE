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
}

export default function SourceBadge({ source }) {
  const label = SOURCE_LABELS[source.source_type] || source.source_type.toUpperCase()
  const color = SOURCE_COLORS[source.source_type] || 'var(--text-muted)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <span className="mono" style={{
        fontSize: '0.6rem',
        letterSpacing: '0.1em',
        padding: '2px 8px',
        border: `1px solid ${color}`,
        color: color,
        background: 'transparent',
      }}>
        {label}
      </span>
      <span className="mono" style={{
        fontSize: '0.6rem',
        color: 'var(--text-muted)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        maxWidth: 200,
      }}>
        {source.retrieval_tool}
      </span>
    </div>
  )
}

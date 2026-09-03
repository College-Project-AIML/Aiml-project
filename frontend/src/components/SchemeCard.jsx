import { Link } from 'react-router-dom'
import { timeAgo } from '../utils'

const styles = {
  card: {
    background: '#141319',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '10px',
    padding: '24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
    transition: 'all 0.2s',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '12px',
  },
  name: {
    fontSize: '1.05rem',
    fontWeight: 600,
    color: '#EEEEF2',
    lineHeight: 1.4,
  },
  badge: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 600,
    background: 'rgba(74,222,128,0.14)',
    color: '#86efac',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  badgeNew: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 700,
    background: '#16a34a',
    color: 'white',
    whiteSpace: 'nowrap',
    flexShrink: 0,
    boxShadow: '0 1px 4px rgba(22,163,74,0.35)',
  },
  badgeClosed: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 600,
    background: 'rgba(220,38,38,0.15)',
    color: '#fca5a5',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  description: {
    fontSize: '0.9rem',
    color: '#6B6F7E',
    lineHeight: 1.6,
    display: '-webkit-box',
    WebkitLineClamp: 3,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  meta: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginTop: 'auto',
  },
  tag: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.75rem',
    fontWeight: 500,
    background: 'rgba(96,165,250,0.12)',
    color: '#93c5fd',
  },
  tagTeal: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.75rem',
    fontWeight: 500,
    background: 'rgba(45,212,191,0.12)',
    color: '#5eead4',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '12px',
    borderTop: '1px solid rgba(255,255,255,0.06)',
  },
  source: {
    fontSize: '0.8rem',
    color: '#45485A',
  },
  link: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#E25822',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
  },
}


function SchemeCard({ scheme }) {
  const stateLabel = scheme.state_code ? scheme.state_code : 'National'
  const updatedAt = scheme.last_updated

  const headerBadge =
    scheme.is_new ? (
      <span style={styles.badgeNew}>NEW</span>
    ) : scheme.status === 'INACTIVE' ? (
      <span style={styles.badgeClosed}>{scheme.status}</span>
    ) : (
      <span style={styles.badge}>{scheme.status || 'ACTIVE'}</span>
    )

  return (
    <div
      style={styles.card}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.6)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.4)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      <div style={styles.header}>
        <Link to={`/schemes/${scheme.id}`} style={styles.name}>
          {scheme.name}
        </Link>
        {headerBadge}
      </div>

      <p style={styles.description}>{scheme.description}</p>

      <div style={styles.meta}>
        {scheme.category_name && <span style={styles.tag}>{scheme.category_name}</span>}
        <span style={styles.tagTeal}>{stateLabel}</span>
        {updatedAt && !scheme.is_new && (
          <span style={{ ...styles.tag, background: 'rgba(96,165,250,0.12)', color: '#93c5fd' }}>
            🔄 Updated {timeAgo(updatedAt)}
          </span>
        )}
        {(scheme.relevance_score || scheme.confidence_score) && (() => {
          const score = scheme.relevance_score || scheme.confidence_score
          const pct = Math.round(score * 100)
          const isRelevance = !!scheme.relevance_score
          const color = isRelevance
            ? (pct >= 80 ? '#6B8F71' : pct >= 60 ? '#B5643A' : '#C49A3C')
            : '#fcd34d'
          const bg = isRelevance ? `${color}18` : 'rgba(251,191,36,0.12)'
          return (
            <span style={{ ...styles.tag, background: bg, color, fontWeight: 600 }}>
              {isRelevance && '⚡ '}{pct}% {isRelevance ? 'match' : 'confidence'}
            </span>
          )
        })()}
      </div>

      <div style={styles.footer}>
        <span style={styles.source}>
          {scheme.provider_name || scheme.source}
        </span>
        <Link to={`/schemes/${scheme.id}`} style={styles.link}>
          View Details →
        </Link>
      </div>
    </div>
  )
}

export default SchemeCard

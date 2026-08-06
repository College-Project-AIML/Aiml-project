import { Link } from 'react-router-dom'
import { timeAgo } from '../utils'

const styles = {
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
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
    color: '#0f4c81',
    lineHeight: 1.4,
  },
  badge: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 600,
    background: '#dcfce7',
    color: '#15803d',
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
    boxShadow: '0 1px 3px rgba(22,163,74,0.4)',
  },
  badgeClosed: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 600,
    background: '#fee2e2',
    color: '#b91c1c',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  description: {
    fontSize: '0.9rem',
    color: '#64748b',
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
    background: '#e0f2fe',
    color: '#0369a1',
  },
  tagTeal: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.75rem',
    fontWeight: 500,
    background: '#ccfbf1',
    color: '#0f766e',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '12px',
    borderTop: '1px solid #f1f5f9',
  },
  source: {
    fontSize: '0.8rem',
    color: '#94a3b8',
  },
  link: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#0f4c81',
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
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.06)'
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
          <span style={{ ...styles.tag, background: '#eff6ff', color: '#1d4ed8' }}>
            🔄 Updated {timeAgo(updatedAt)}
          </span>
        )}
        {scheme.confidence_score && (
          <span style={{ ...styles.tag, background: '#fef3c7', color: '#92400e' }}>
            {Math.round(scheme.confidence_score * 100)}% confidence
          </span>
        )}
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

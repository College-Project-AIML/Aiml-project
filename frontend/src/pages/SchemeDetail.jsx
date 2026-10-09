import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getScheme } from '../api/api'
import { timeAgo, formatValue } from '../utils'
import { useAuth } from '../context/AuthContext'
import { getApplications, trackApplication } from '../utils/applicationTracker'

const styles = {
  content: {
    maxWidth: '900px',
    margin: '0 auto',
    padding: '0 24px 60px',
  },
  back: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    color: 'rgba(255,255,255,0.65)',
    fontSize: '0.9rem',
    marginBottom: '16px',
    transition: 'color 0.2s',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 700,
    marginBottom: '12px',
    letterSpacing: '-0.02em',
    color: '#EEEEF2',
  },
  metaRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
    marginBottom: '0',
  },
  section: {
    marginBottom: '32px',
  },
  sectionTitle: {
    fontSize: '1.15rem',
    fontWeight: 700,
    color: '#EEEEF2',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  card: {
    background: '#141319',
    border: '0.5px solid rgba(255,255,255,0.08)',
    borderRadius: '10px',
    padding: '24px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.4)',
  },
  description: {
    fontSize: '1rem',
    lineHeight: 1.7,
    color: '#9A988F',
  },
  eligText: {
    fontSize: '0.95rem',
    lineHeight: 1.7,
    color: '#9A988F',
    padding: '16px',
    background: '#0F0F14',
    borderRadius: '8px',
    border: '0.5px solid rgba(255,255,255,0.08)',
  },
  ruleGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '12px',
  },
  ruleItem: {
    padding: '14px',
    background: 'rgba(96,165,250,0.07)',
    borderRadius: '8px',
    border: '0.5px solid rgba(96,165,250,0.18)',
  },
  ruleLabel: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#6B6F7E',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '4px',
  },
  ruleValue: {
    fontSize: '0.95rem',
    fontWeight: 600,
    color: '#93c5fd',
  },
  benefitItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 0',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  benefitType: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#5eead4',
    background: 'rgba(45,212,191,0.1)',
    padding: '2px 8px',
    borderRadius: '4px',
    marginBottom: '4px',
    display: 'inline-block',
  },
  benefitDesc: {
    fontSize: '0.9rem',
    color: '#9A988F',
  },
  benefitAmount: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: '#EEEEF2',
    whiteSpace: 'nowrap',
  },
  docList: {
    listStyle: 'none',
    padding: 0,
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '8px',
  },
  docItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 14px',
    background: '#0F0F14',
    borderRadius: '6px',
    border: '0.5px solid rgba(255,255,255,0.07)',
    fontSize: '0.9rem',
    color: '#9A988F',
  },
  tags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginTop: '12px',
  },
  sidebar: {
    display: 'grid',
    gridTemplateColumns: '1fr 300px',
    gap: '32px',
    alignItems: 'start',
  },
  infoBox: {
    background: '#141319',
    border: '0.5px solid rgba(255,255,255,0.08)',
    borderRadius: '10px',
    padding: '20px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.4)',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    fontSize: '0.9rem',
  },
  infoLabel: {
    color: '#6B6F7E',
    fontWeight: 500,
  },
  infoValue: {
    color: '#EEEEF2',
    fontWeight: 600,
    textAlign: 'right',
  },
  changePanel: {
    background: 'rgba(96,165,250,0.05)',
    border: '0.5px solid rgba(96,165,250,0.18)',
    borderRadius: '10px',
    padding: '20px 24px',
  },
  changeHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '14px',
  },
  changeTypeBadge: {
    padding: '3px 10px',
    borderRadius: '100px',
    fontSize: '0.72rem',
    fontWeight: 700,
    background: 'rgba(96,165,250,0.15)',
    color: '#93c5fd',
  },
  changeTime: {
    fontSize: '0.8rem',
    color: '#6B6F7E',
  },
  changeField: {
    display: 'grid',
    gridTemplateColumns: '150px 1fr 1fr',
    gap: '12px',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    fontSize: '0.85rem',
  },
  changeFieldName: {
    fontWeight: 600,
    color: '#9A988F',
    textTransform: 'capitalize',
  },
  changeOld: {
    color: '#fca5a5',
    textDecoration: 'line-through',
    opacity: 0.8,
  },
  changeNew: {
    color: '#86efac',
    fontWeight: 600,
  },
}

function formatAmount(amount) {
  if (!amount) return '—'
  return `₹${Number(amount).toLocaleString('en-IN')}`
}

function SchemeDetail() {
  const { id } = useParams()
  const [scheme, setScheme] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { user } = useAuth()
  const [isTracked, setIsTracked] = useState(false)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const data = await getScheme(id)
        setScheme(data)
        if (user) {
          const userKey = user.user_id || user.email
          setIsTracked(getApplications(userKey).some((application) => application.scheme.id === data.id))
        }
      } catch (err) {
        setError('Scheme not found')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, user])

  const handleTrackApplication = () => {
    if (!user) return
    trackApplication(user.user_id || user.email, scheme)
    setIsTracked(true)
  }

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '400px' }}>
        <div className="spinner" />
        Loading scheme details...
      </div>
    )
  }

  if (error || !scheme) {
    return (
      <div className="empty-state" style={{ minHeight: '400px' }}>
        <h3>{error || 'Scheme not found'}</h3>
        <Link to="/schemes" className="btn btn-outline" style={{ marginTop: '16px' }}>
          ← Back to Schemes
        </Link>
      </div>
    )
  }

  const rules = scheme.eligibility_rules || []
  const benefits = scheme.benefits || []
  const documents = scheme.documents_required || []
  const latestUpdate = scheme.latest_update
  const changedFields = (latestUpdate && latestUpdate.changed_fields) || {}
  const changeFieldKeys = Object.keys(changedFields)

  return (
    <div>
      <div className="page-header">
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <Link to="/schemes" style={styles.back}>← Back to Schemes</Link>
          <h1 style={styles.title}>{scheme.name}</h1>
          <div style={styles.metaRow}>
            {scheme.category_name && <span className="tag">{scheme.category_name}</span>}
            <span className="tag tag-teal">{scheme.state_code || 'National'}</span>
            <span className={`badge ${scheme.status === 'ACTIVE' ? 'badge-active' : 'badge-inactive'}`}>
              {scheme.status}
            </span>
            {scheme.confidence_score && (
              <span className="tag tag-amber">
                {Math.round(scheme.confidence_score * 100)}% confidence
              </span>
            )}
          </div>
          {user && (
            <button
              type="button"
              onClick={handleTrackApplication}
              disabled={isTracked}
              className="btn btn-primary"
              style={{ marginTop: '18px', opacity: isTracked ? 0.7 : 1, cursor: isTracked ? 'default' : 'pointer' }}
            >
              {isTracked ? '✓ Added to Applications' : 'Track Application'}
            </button>
          )}
        </div>
      </div>

      <div style={styles.content}>
        {latestUpdate && changeFieldKeys.length > 0 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>🔄 What Changed</h2>
            <div style={styles.changePanel}>
              <div style={styles.changeHeader}>
                <span style={styles.changeTypeBadge}>{latestUpdate.change_type}</span>
                <span style={styles.changeTime}>Detected {timeAgo(latestUpdate.detected_at)}</span>
              </div>
              {changeFieldKeys.map((field) => {
                const [oldValue, newValue] = changedFields[field] || []
                return (
                  <div key={field} style={styles.changeField}>
                    <span style={styles.changeFieldName}>{formatValue(field)}</span>
                    <span style={styles.changeOld}>{formatValue(oldValue)}</span>
                    <span style={styles.changeNew}>→ {formatValue(newValue)}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>📋 Description</h2>
          <div style={styles.card}>
            <p style={styles.description}>{scheme.description}</p>
          </div>
        </div>

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>✅ Eligibility</h2>
          <div style={styles.eligText}>{scheme.eligibility_text || 'Eligibility details not specified.'}</div>

          <div style={{ marginTop: '16px' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#6B6F7E', marginBottom: '10px' }}>
              Structured Eligibility Criteria
            </div>
            {(rules.length > 0 ? rules : [{}]).map((r, i) => (
              <div key={i} style={styles.ruleGrid}>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Min Age</div>
                  <div style={styles.ruleValue}>{r.min_age != null ? `${r.min_age} years` : 'N/A'}</div>
                </div>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Max Age</div>
                  <div style={styles.ruleValue}>{r.max_age != null ? `${r.max_age} years` : 'N/A'}</div>
                </div>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Max Income</div>
                  <div style={styles.ruleValue}>{r.max_income != null ? `${formatAmount(r.max_income)}/yr` : 'N/A'}</div>
                </div>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Gender</div>
                  <div style={styles.ruleValue}>{r.gender && r.gender.length > 0 ? r.gender.join(', ') : 'N/A'}</div>
                </div>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Category</div>
                  <div style={styles.ruleValue}>{r.caste && r.caste.length > 0 ? r.caste.join(', ') : 'N/A'}</div>
                </div>
                <div style={styles.ruleItem}>
                  <div style={styles.ruleLabel}>Education</div>
                  <div style={styles.ruleValue}>{r.education_level ? r.education_level.replace(/_/g, ' ') : 'N/A'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>💰 Benefits</h2>
          <div style={styles.card}>
            {benefits.length > 0 ? (
              benefits.map((b, i) => (
                <div key={i} style={{ ...styles.benefitItem, borderBottom: i < benefits.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                  <div>
                    <span style={styles.benefitType}>{(b.benefit_type || '').replace(/_/g, ' ')}</span>
                    <div style={styles.benefitDesc}>{b.description}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={styles.benefitAmount}>{formatAmount(b.amount)}</div>
                    {b.frequency && (
                      <div style={{ fontSize: '0.8rem', color: '#6B6F7E' }}>{b.frequency}</div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p style={{ ...styles.description, margin: 0 }}>Benefits details not specified.</p>
            )}
          </div>
        </div>

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>📄 Required Documents</h2>
          {documents.length > 0 ? (
            <ul style={styles.docList}>
              {documents.map((d, i) => (
                <li key={i} style={styles.docItem}>
                  <span style={{ color: d.is_mandatory ? '#4ade80' : '#45485A' }}>
                    {d.is_mandatory ? '●' : '○'}
                  </span>
                  {d.document_name}
                  {!d.is_mandatory && (
                    <span style={{ fontSize: '0.75rem', color: '#45485A' }}>(optional)</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div style={styles.card}>
              <p style={{ ...styles.description, margin: 0 }}>Required documents not specified.</p>
            </div>
          )}
        </div>

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>ℹ️ Additional Information</h2>
          <div style={styles.infoBox}>
            {scheme.provider_name && (
              <div style={styles.infoRow}>
                <span style={styles.infoLabel}>Provider</span>
                <span style={styles.infoValue}>{scheme.provider_name}</span>
              </div>
            )}
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Source</span>
              <span style={styles.infoValue}>{scheme.source}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Coverage</span>
              <span style={styles.infoValue}>{scheme.state_code || 'All India'}</span>
            </div>
            {scheme.link && (
              <div style={{ ...styles.infoRow, borderBottom: 'none' }}>
                <span style={styles.infoLabel}>Official Link</span>
                <a href={scheme.link} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 600, color: '#E25822' }}>
                  Visit ↗
                </a>
              </div>
            )}
          </div>
        </div>

        {scheme.tags && scheme.tags.length > 0 && (
          <div style={styles.tags}>
            {scheme.tags.map((t, i) => (
              <span key={i} className="tag">{t}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SchemeDetail

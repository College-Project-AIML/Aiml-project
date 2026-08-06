import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getScheme } from '../api/api'
import { timeAgo, formatValue } from '../utils'

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
    color: 'rgba(255,255,255,0.8)',
    fontSize: '0.9rem',
    marginBottom: '16px',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 700,
    marginBottom: '12px',
    letterSpacing: '-0.02em',
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
    color: '#0f172a',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  description: {
    fontSize: '1rem',
    lineHeight: 1.7,
    color: '#334155',
  },
  eligText: {
    fontSize: '0.95rem',
    lineHeight: 1.7,
    color: '#475569',
    padding: '16px',
    background: '#f8fafc',
    borderRadius: '8px',
    border: '1px solid #e2e8f0',
  },
  ruleGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '12px',
  },
  ruleItem: {
    padding: '14px',
    background: '#f0f9ff',
    borderRadius: '8px',
    border: '1px solid #bae6fd',
  },
  ruleLabel: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '4px',
  },
  ruleValue: {
    fontSize: '0.95rem',
    fontWeight: 600,
    color: '#0c4a6e',
  },
  benefitItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 0',
    borderBottom: '1px solid #f1f5f9',
  },
  benefitType: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#0d9488',
    background: '#ccfbf1',
    padding: '2px 8px',
    borderRadius: '4px',
    marginBottom: '4px',
    display: 'inline-block',
  },
  benefitDesc: {
    fontSize: '0.9rem',
    color: '#334155',
  },
  benefitAmount: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: '#0f4c81',
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
    background: '#f8fafc',
    borderRadius: '6px',
    fontSize: '0.9rem',
    color: '#334155',
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
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: '1px solid #f1f5f9',
    fontSize: '0.9rem',
  },
  infoLabel: {
    color: '#64748b',
    fontWeight: 500,
  },
  infoValue: {
    color: '#1e293b',
    fontWeight: 600,
    textAlign: 'right',
  },
  changePanel: {
    background: 'linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%)',
    border: '1px solid #dbeafe',
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
    background: '#dbeafe',
    color: '#1d4ed8',
  },
  changeTime: {
    fontSize: '0.8rem',
    color: '#64748b',
  },
  changeField: {
    display: 'grid',
    gridTemplateColumns: '150px 1fr 1fr',
    gap: '12px',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: '1px solid #e2e8f0',
    fontSize: '0.85rem',
  },
  changeFieldName: {
    fontWeight: 600,
    color: '#475569',
    textTransform: 'capitalize',
  },
  changeOld: {
    color: '#b91c1c',
    textDecoration: 'line-through',
    opacity: 0.8,
  },
  changeNew: {
    color: '#15803d',
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

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const data = await getScheme(id)
        setScheme(data)
      } catch (err) {
        setError('Scheme not found')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

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
          <div style={styles.eligText}>{scheme.eligibility_text}</div>

          {rules.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748b', marginBottom: '10px' }}>
                Structured Eligibility Criteria
              </div>
              {rules.map((r, i) => (
                <div key={i} style={styles.ruleGrid}>
                  {r.min_age != null && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Min Age</div>
                      <div style={styles.ruleValue}>{r.min_age} years</div>
                    </div>
                  )}
                  {r.max_age != null && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Max Age</div>
                      <div style={styles.ruleValue}>{r.max_age} years</div>
                    </div>
                  )}
                  {r.max_income != null && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Max Income</div>
                      <div style={styles.ruleValue}>{formatAmount(r.max_income)}/yr</div>
                    </div>
                  )}
                  {r.gender && r.gender.length > 0 && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Gender</div>
                      <div style={styles.ruleValue}>{r.gender.join(', ')}</div>
                    </div>
                  )}
                  {r.caste && r.caste.length > 0 && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Category</div>
                      <div style={styles.ruleValue}>{r.caste.join(', ')}</div>
                    </div>
                  )}
                  {r.states && r.states.length > 0 && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>States</div>
                      <div style={styles.ruleValue}>{r.states.join(', ')}</div>
                    </div>
                  )}
                  {r.education_level && (
                    <div style={styles.ruleItem}>
                      <div style={styles.ruleLabel}>Education</div>
                      <div style={styles.ruleValue}>{r.education_level.replace(/_/g, ' ')}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {benefits.length > 0 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>💰 Benefits</h2>
            <div style={styles.card}>
              {benefits.map((b, i) => (
                <div key={i} style={{ ...styles.benefitItem, borderBottom: i < benefits.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                  <div>
                    <span style={styles.benefitType}>{(b.benefit_type || '').replace(/_/g, ' ')}</span>
                    <div style={styles.benefitDesc}>{b.description}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={styles.benefitAmount}>{formatAmount(b.amount)}</div>
                    {b.frequency && (
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{b.frequency}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {documents.length > 0 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>📄 Required Documents</h2>
            <ul style={styles.docList}>
              {documents.map((d, i) => (
                <li key={i} style={styles.docItem}>
                  <span style={{ color: d.is_mandatory ? '#16a34a' : '#94a3b8' }}>
                    {d.is_mandatory ? '●' : '○'}
                  </span>
                  {d.document_name}
                  {!d.is_mandatory && (
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>(optional)</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

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
                <a href={scheme.link} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 600 }}>
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

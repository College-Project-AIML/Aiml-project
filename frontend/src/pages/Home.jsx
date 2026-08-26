import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getSchemes, getCategories, getStats, getUpdates } from '../api/api'
import { timeAgo } from '../utils'
import SchemeCard from '../components/SchemeCard'

const CATEGORY_THEMES = {
  Scholarship: { tint: 'var(--tint-saffron)', color: 'var(--accent)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg> },
  Fellowship: { tint: 'var(--tint-navy)', color: 'var(--primary)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" /><path d="M2 12h20" /></svg> },
  Grant: { tint: 'var(--tint-green)', color: 'var(--success)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg> },
  Loan: { tint: 'var(--tint-purple)', color: '#7e22ce', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" /></svg> },
  Subsidy: { tint: 'var(--tint-yellow)', color: 'var(--warning)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01" /></svg> },
  'Skill Program': { tint: 'var(--tint-blue)', color: '#0284c7', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg> },
  'Welfare Scheme': { tint: 'var(--tint-rose)', color: '#e11d48', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg> },
  OTHER: { tint: 'var(--bg)', color: 'var(--text-secondary)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg> }
}

const styles = {
  hero: {
    background: '#FBF8F1',
    padding: '56px 0 40px',
    textAlign: 'center',
    width: '100%',
  },
  heroInner: {
    maxWidth: '640px',
    width: '90%',
    margin: '0 auto',
  },
  kicker: {
    color: '#A9642B',
    fontSize: '11.5px',
    fontWeight: 'normal',
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    marginBottom: '14px',
    display: 'block',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  heroTitle: {
    fontSize: 'clamp(28px, 4vw, 40px)',
    fontWeight: 400,
    marginBottom: '16px',
    lineHeight: 1.25,
    color: '#1B2A4A',
    fontFamily: "Georgia, 'Lora', 'Playfair Display', serif",
    maxWidth: '430px',
    margin: '0 auto 16px auto',
  },
  heroSub: {
    color: '#5B5748',
    fontSize: 'clamp(14px, 2.5vw, 15px)',
    lineHeight: 1.5,
    marginBottom: '28px',
    maxWidth: '440px',
    margin: '0 auto 28px auto',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  searchBarContainer: {
    display: 'flex',
    flexDirection: 'row',
    maxWidth: '100%',
    margin: '0 auto',
    height: '42px',
    boxSizing: 'border-box',
  },
  searchInput: {
    flex: 1,
    height: '42px',
    padding: '0 12px',
    fontSize: '13px',
    border: '1.5px solid #1B2A4A',
    borderRight: 'none',
    background: '#FFFFFF',
    color: '#5B5748',
    outline: 'none',
    borderRadius: '2px 0 0 2px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    boxSizing: 'border-box',
    minWidth: 0,
  },
  searchBtn: {
    height: '42px',
    padding: '0 24px',
    background: '#1B2A4A',
    color: '#FBF8F1',
    fontSize: '14px',
    fontWeight: 'normal',
    border: '1.5px solid #1B2A4A',
    cursor: 'pointer',
    borderRadius: '0 2px 2px 0',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    boxSizing: 'border-box',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: 0,
  },
  section: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '60px 24px',
  },
  sectionTitle: {
    fontSize: '1.75rem',
    fontWeight: 700,
    marginBottom: '8px',
    color: 'var(--primary)',
    fontFamily: "'Eczar', serif",
  },
  sectionSub: {
    color: 'var(--text-secondary)',
    marginBottom: '32px',
    fontSize: '1.05rem',
  },
  catGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: '20px',
  },
  catCard: {
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    overflow: 'hidden',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    textDecoration: 'none',
    boxShadow: 'var(--shadow)',
  },
  catHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },
  catIconArea: {
    width: '48px',
    height: '48px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  catName: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: 'var(--primary)',
  },
  catBody: {
    borderTop: '1px solid var(--border)',
    paddingTop: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  catCount: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    fontWeight: '500',
  },
  catLink: {
    fontSize: '0.85rem',
    fontWeight: '600',
    color: 'var(--accent)',
  },
  schemeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
    gap: '20px',
  },
  viewAll: {
    textAlign: 'center',
    marginTop: '40px',
  },
  updatesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  updateRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '16px 20px',
    transition: 'all 0.2s',
    textDecoration: 'none',
    color: 'inherit',
    boxShadow: 'var(--shadow)',
  },
  updateTag: {
    padding: '4px 12px',
    borderRadius: '100px',
    fontSize: '0.75rem',
    fontWeight: 700,
    background: 'var(--tint-green)',
    color: 'var(--success)',
    whiteSpace: 'nowrap',
    flexShrink: 0,
    border: '1px solid rgba(22, 101, 52, 0.2)',
  },
  updateName: {
    flex: 1,
    fontWeight: 600,
    color: 'var(--primary)',
    fontSize: '1rem',
  },
  updateTime: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    whiteSpace: 'nowrap',
  },
}

function Home() {
  const navigate = useNavigate()
  const [schemes, setSchemes] = useState([])
  const [categories, setCategories] = useState([])
  const [updates, setUpdates] = useState([])
  const [totalSchemes, setTotalSchemes] = useState(0)
  const [totalStates, setTotalStates] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [schemesRes, catsRes] = await Promise.all([
          getSchemes({ limit: 6 }),
          getCategories(),
        ])
        setSchemes(schemesRes.schemes)
        setTotalSchemes(schemesRes.total)
        setCategories(catsRes.filter(c => c.name !== 'Training Program'))

        getStats()
          .then((s) => {
            setTotalSchemes(s.total_schemes)
            setTotalStates(s.total_states)
          })
          .catch((err) => console.error('Failed to load stats:', err))
      } catch (err) {
        console.error('Failed to load home data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    getUpdates({ limit: 5 })
      .then((res) => setUpdates(res.updates || []))
      .catch(() => setUpdates([]))
  }, [])

  const handleSearch = (query) => {
    if (!query) return;
    navigate(`/schemes?q=${encodeURIComponent(query)}`)
  }

  return (
    <div>
      <div style={styles.hero}>
        <div style={styles.heroInner}>
          <span style={styles.kicker}>
            GOVERNMENT SCHEME REGISTRY · KARNATAKA
          </span>
          <h1 style={styles.heroTitle}>
            Find the scheme you already qualify for
          </h1>
          <p style={styles.heroSub}>
            Verified scholarship, subsidy, and welfare data pulled straight from central and state government sources.
          </p>

          <div style={styles.searchBarContainer}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch(searchQuery)
              }}
              placeholder="Search by name, category, or eligibility..."
              style={styles.searchInput}
            />
            <button
              style={styles.searchBtn}
              onClick={() => handleSearch(searchQuery)}
              onMouseEnter={(e) => { e.target.style.background = '#2B4270'; e.target.style.borderColor = '#2B4270'; }}
              onMouseLeave={(e) => { e.target.style.background = '#1B2A4A'; e.target.style.borderColor = '#1B2A4A'; }}
            >
              Search
            </button>
          </div>
        </div>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Browse Directory</h2>
        <p style={styles.sectionSub}>Explore schemes categorized by official departments</p>
        <div style={styles.catGrid}>
          {categories.map((cat) => {
            const theme = CATEGORY_THEMES[cat.name] || CATEGORY_THEMES['OTHER']
            return (
              <Link
                key={cat.id}
                to={`/schemes?category=${encodeURIComponent(cat.name)}`}
                style={styles.catCard}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)'
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'var(--shadow)'
                }}
              >
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: theme.color }} />
                <div style={styles.catHeader}>
                  <div style={{ ...styles.catIconArea, background: theme.tint, color: theme.color }}>
                    {theme.icon}
                  </div>
                  <div style={styles.catName}>{cat.name}</div>
                </div>
                <div style={styles.catBody}>
                  <div style={styles.catCount}>{cat.scheme_count} active programs</div>
                  <div style={{ ...styles.catLink, color: theme.color }}>View →</div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {updates.length > 0 && (
        <div style={{ ...styles.section, background: 'var(--bg-card)', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '32px' }}>
              <div>
                <h2 style={styles.sectionTitle}>Latest Updates</h2>
                <p style={{ ...styles.sectionSub, marginBottom: 0 }}>System-detected changes from government portals</p>
              </div>
              <Link to="/schemes?sort=recently_updated" className="btn btn-outline" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
                View All Updates →
              </Link>
            </div>
            <div style={styles.updatesList}>
              {updates.map((u) => {
                const tagColor = u.change_type === 'CLOSED' ? '#dc2626' : 'var(--success)'
                const tagBg = u.change_type === 'CLOSED' ? '#fef2f2' : 'var(--tint-green)'
                const tagBorder = u.change_type === 'CLOSED' ? 'rgba(220, 38, 38, 0.2)' : 'rgba(22, 101, 52, 0.2)'
                return (
                  <Link
                    key={`${u.scheme?.id || 'scheme'}-${u.detected_at || 'time'}`}
                    to={`/schemes/${u.scheme?.id}`}
                    style={styles.updateRow}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(6px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateX(0)'}
                  >
                    <span style={{ ...styles.updateTag, background: tagBg, color: tagColor, borderColor: tagBorder }}>
                      {u.change_type}
                    </span>
                    <span style={styles.updateName}>{u.scheme?.name || 'Scheme'}</span>
                    <span style={styles.updateTime}>{timeAgo(u.detected_at)}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}

      <div style={styles.section}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={styles.sectionTitle}>Featured Schemes</h2>
          <p style={styles.sectionSub}>Recently verified government programs</p>
          {loading ? (
            <div className="loading">
              <div className="spinner" />
              Loading schemes...
            </div>
          ) : (
            <>
              <div style={styles.schemeGrid}>
                {schemes.map((s) => (
                  <SchemeCard key={s.id} scheme={s} />
                ))}
              </div>
              <div style={styles.viewAll}>
                <Link to="/schemes" className="btn btn-primary">
                  Browse All {totalSchemes || ''} Schemes →
                </Link>
              </div>
            </>
          )}
        </div>
      </div>

      <div style={{ ...styles.section, paddingBottom: '100px' }}>
        <div style={{
          background: 'var(--primary)',
          borderRadius: 'var(--radius)',
          padding: '60px 40px',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '40px',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <div style={{ maxWidth: '500px' }}>
            <h2 style={{ fontSize: '2rem', fontFamily: "'Eczar', serif", marginBottom: '16px' }}>Check Your Eligibility</h2>
            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.1rem', marginBottom: '32px', lineHeight: 1.6 }}>
              Enter your profile details to match against structured eligibility criteria from official sources.
              <br /><br />
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#68d391' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                Privacy-first: No data is stored or shared.
              </span>
            </p>
            <Link to="/eligibility" className="btn btn-accent" style={{ fontSize: '1.05rem', padding: '14px 32px' }}>
              Check Eligibility Free →
            </Link>
          </div>
          <div style={{ flex: 1, minWidth: '300px', display: 'flex', justifyContent: 'center' }}>
            <div style={{ maxWidth: '100%' }}>
              {/* Visual representation of a card stack */}
              <div style={{
                background: 'white', color: 'var(--text)', padding: '24px', borderRadius: '12px',
                boxShadow: '10px 10px 0px rgba(226, 88, 34, 0.2)', // Heritage Saffron shadow
                transform: 'rotate(2deg)'
              }}>
                <div style={{ height: '8px', width: '40px', background: 'var(--tint-blue)', borderRadius: '4px', marginBottom: '16px' }} />
                <div style={{ fontSize: '1.2rem', fontFamily: "'Eczar', serif", fontWeight: 700, marginBottom: '8px' }}>
                  Post-Matric Scholarship
                </div>
                <div style={{ height: '6px', width: '80%', background: 'var(--border)', borderRadius: '3px', marginBottom: '8px' }} />
                <div style={{ height: '6px', width: '60%', background: 'var(--border)', borderRadius: '3px', marginBottom: '24px' }} />
                <div style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 600 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  Matched your profile
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home

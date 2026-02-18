import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getSchemes, getCategories, searchSchemes } from '../api/api'
import SchemeCard from '../components/SchemeCard'
import SearchBar from '../components/SearchBar'

const styles = {
  hero: {
    background: 'linear-gradient(135deg, #0a3560 0%, #0f4c81 50%, #0d7377 100%)',
    color: 'white',
    padding: '64px 24px',
    textAlign: 'center',
  },
  heroInner: {
    maxWidth: '720px',
    margin: '0 auto',
  },
  heroTitle: {
    fontSize: '2.5rem',
    fontWeight: 700,
    marginBottom: '16px',
    letterSpacing: '-0.03em',
    lineHeight: 1.2,
  },
  heroSub: {
    fontSize: '1.1rem',
    color: 'rgba(255,255,255,0.8)',
    marginBottom: '32px',
    lineHeight: 1.6,
  },
  statsRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '48px',
    marginTop: '36px',
  },
  stat: {
    textAlign: 'center',
  },
  statNum: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#5eead4',
  },
  statLabel: {
    fontSize: '0.85rem',
    color: 'rgba(255,255,255,0.7)',
    marginTop: '4px',
  },
  section: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '40px 24px',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 700,
    marginBottom: '8px',
    color: '#0f172a',
  },
  sectionSub: {
    color: '#64748b',
    marginBottom: '24px',
    fontSize: '0.95rem',
  },
  catGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: '16px',
  },
  catCard: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    textDecoration: 'none',
    color: 'inherit',
  },
  catName: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#0f4c81',
  },
  catCount: {
    fontSize: '0.85rem',
    color: '#64748b',
  },
  schemeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
    gap: '20px',
  },
  viewAll: {
    textAlign: 'center',
    marginTop: '32px',
  },
}

const ICONS = {
  Scholarship: '🎓',
  Fellowship: '🔬',
  Grant: '💰',
  Loan: '🏦',
  Subsidy: '🏷️',
  'Skill Program': '⚡',
  'Training Program': '📚',
  'Welfare Scheme': '🤝',
}

function Home() {
  const navigate = useNavigate()
  const [schemes, setSchemes] = useState([])
  const [categories, setCategories] = useState([])
  const [totalSchemes, setTotalSchemes] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [schemesRes, catsRes] = await Promise.all([
          getSchemes({ limit: 6 }),
          getCategories(),
        ])
        setSchemes(schemesRes.schemes)
        setTotalSchemes(schemesRes.total)
        setCategories(catsRes)
      } catch (err) {
        console.error('Failed to load home data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleSearch = (query) => {
    navigate(`/schemes?q=${encodeURIComponent(query)}`)
  }

  return (
    <div>
      <div style={styles.hero}>
        <div style={styles.heroInner}>
          <h1 style={styles.heroTitle}>Discover Government Schemes</h1>
          <p style={styles.heroSub}>
            Find scholarships, welfare programs, subsidies, and more.
            Structured data from central and state government sources.
          </p>
          <SearchBar
            onSearch={handleSearch}
            placeholder="Search scholarships, welfare schemes, subsidies..."
          />
          <div style={styles.statsRow}>
            <div style={styles.stat}>
              <div style={styles.statNum}>{totalSchemes}</div>
              <div style={styles.statLabel}>Schemes</div>
            </div>
            <div style={styles.stat}>
              <div style={styles.statNum}>{categories.length}</div>
              <div style={styles.statLabel}>Categories</div>
            </div>
            <div style={styles.stat}>
              <div style={styles.statNum}>
                {categories.reduce((sum, c) => sum + (c.scheme_count || 0), 0) > 0 ? '2' : '0'}
              </div>
              <div style={styles.statLabel}>States</div>
            </div>
          </div>
        </div>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Browse by Category</h2>
        <p style={styles.sectionSub}>Explore schemes organized by type</p>
        <div style={styles.catGrid}>
          {categories.map((cat) => (
            <Link
              key={cat.id}
              to={`/schemes?category=${encodeURIComponent(cat.name)}`}
              style={styles.catCard}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'
                e.currentTarget.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              <span style={{ fontSize: '1.5rem' }}>{ICONS[cat.name] || '📋'}</span>
              <span style={styles.catName}>{cat.name}</span>
              <span style={styles.catCount}>{cat.scheme_count} schemes</span>
            </Link>
          ))}
        </div>
      </div>

      <div style={{ ...styles.section, background: '#f1f5f9', padding: '40px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={styles.sectionTitle}>Featured Schemes</h2>
          <p style={styles.sectionSub}>Recently added government programs</p>
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
                <Link to="/schemes" className="btn btn-outline">
                  View All Schemes →
                </Link>
              </div>
            </>
          )}
        </div>
      </div>

      <div style={styles.section}>
        <div style={{ display: 'flex', gap: '32px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
          <div style={{ maxWidth: '400px' }}>
            <h2 style={styles.sectionTitle}>Check Your Eligibility</h2>
            <p style={{ color: '#64748b', marginBottom: '20px', lineHeight: 1.6 }}>
              Enter your profile details and discover which schemes you qualify for.
              Simple, fast, and privacy-first — no data is stored.
            </p>
            <Link to="/eligibility" className="btn btn-accent">
              Check Eligibility →
            </Link>
          </div>
          <div style={{
            background: 'linear-gradient(135deg, #0d9488 0%, #0f4c81 100%)',
            borderRadius: '12px',
            padding: '40px',
            color: 'white',
            maxWidth: '320px',
            width: '100%',
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🎯</div>
            <div style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: '8px' }}>
              Personalized Matching
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.85 }}>
              Our rule engine matches your profile against structured eligibility criteria from government sources.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home

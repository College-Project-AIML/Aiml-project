import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { getSchemes, getCategories, getStats, getUpdates } from '../api/api'
import { timeAgo } from '../utils'
import SchemeCard from '../components/SchemeCard'
import ParticleCanvas from '../components/ParticleCanvas'

// ── Scroll-reveal wrapper ───────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

function RevealSection({ children, style, className }) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: '-100px' }}
      style={style}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ── Horizontal scroll row ────────────────────────────────────────────────────
function HScrollRow({ schemes }) {
  const rowRef = useRef(null)
  const [fillPct, setFillPct] = useState(0)

  const scroll = (dir) => {
    if (!rowRef.current) return
    rowRef.current.scrollBy({ left: dir * 380, behavior: 'smooth' })
  }

  const onScroll = () => {
    const el = rowRef.current
    if (!el) return
    const max = el.scrollWidth - el.clientWidth
    setFillPct(max > 0 ? (el.scrollLeft / max) * 100 : 0)
  }

  return (
    <div className="hscroll-wrapper">
      <button className="hscroll-arrow left" onClick={() => scroll(-1)} aria-label="Scroll left">‹</button>
      <div className="hscroll-row" ref={rowRef} onScroll={onScroll}>
        {schemes.map((s) => <SchemeCard key={s.id} scheme={s} />)}
      </div>
      <button className="hscroll-arrow right" onClick={() => scroll(1)} aria-label="Scroll right">›</button>
      <div className="hscroll-track">
        <div className="hscroll-fill" style={{ width: `${fillPct}%` }} />
      </div>
    </div>
  )
}

// ── Category themes ──────────────────────────────────────────────────────────
const CATEGORY_THEMES = {
  Scholarship: { tint: 'var(--tint-saffron)', color: 'var(--accent)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg> },
  Fellowship: { tint: 'var(--tint-navy)', color: '#93B8E8', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" /><path d="M2 12h20" /></svg> },
  Grant: { tint: 'var(--tint-green)', color: 'var(--success)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg> },
  Loan: { tint: 'var(--tint-purple)', color: '#A78BFA', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" /></svg> },
  Subsidy: { tint: 'var(--tint-yellow)', color: 'var(--warning)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82zM7 7h.01" /></svg> },
  'Skill Program': { tint: 'var(--tint-blue)', color: '#60A5FA', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg> },
  'Welfare Scheme': { tint: 'var(--tint-rose)', color: '#F87171', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg> },
  OTHER: { tint: 'var(--tint-navy)', color: 'var(--text-secondary)', icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg> },
}

const styles = {
  section: { maxWidth: '1200px', margin: '0 auto', padding: '60px 24px' },
  sectionTitle: { fontSize: '1.75rem', fontWeight: 700, marginBottom: '8px', color: '#EDEFF5', fontFamily: "'Eczar', serif" },
  sectionSub: { color: '#8890A6', marginBottom: '32px', fontSize: '1.05rem' },
  catGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '20px' },
  catCard: { background: '#182240', border: '1px solid #26304F', borderRadius: '12px', padding: '24px', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', cursor: 'pointer', transition: 'all 0.2s ease', textDecoration: 'none', boxShadow: '0 1px 4px rgba(0,0,0,0.45)' },
  catHeader: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' },
  catIconArea: { width: '48px', height: '48px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  catName: { fontSize: '1.1rem', fontWeight: 700, color: '#EDEFF5' },
  catBody: { borderTop: '1px solid #26304F', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  catCount: { fontSize: '0.85rem', color: '#8890A6', fontWeight: 500 },
  viewAll: { textAlign: 'center', marginTop: '40px' },
  updatesList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  updateRow: { display: 'flex', alignItems: 'center', gap: '16px', background: '#182240', border: '1px solid #26304F', borderRadius: '12px', padding: '16px 20px', transition: 'all 0.2s', textDecoration: 'none', color: 'inherit', boxShadow: '0 1px 4px rgba(0,0,0,0.4)' },
  updateTag: { padding: '4px 12px', borderRadius: '100px', fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap', flexShrink: 0 },
  updateName: { flex: 1, fontWeight: 600, color: '#EDEFF5', fontSize: '1rem' },
  updateTime: { fontSize: '0.85rem', color: '#8890A6', whiteSpace: 'nowrap' },
}

function Home() {
  const navigate = useNavigate()
  const [schemes, setSchemes] = useState([])
  const [categories, setCategories] = useState([])
  const [updates, setUpdates] = useState([])
  const [totalSchemes, setTotalSchemes] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [schemesRes, catsRes] = await Promise.all([getSchemes({ limit: 8 }), getCategories()])
        setSchemes(schemesRes.schemes)
        setTotalSchemes(schemesRes.total)
        setCategories(catsRes.filter(c => c.name !== 'Training Program'))
        getStats().then(s => { setTotalSchemes(s.total_schemes) }).catch(() => { })
      } catch (err) {
        console.error('Failed to load home data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    getUpdates({ limit: 5 }).then(res => setUpdates(res.updates || [])).catch(() => setUpdates([]))
  }, [])

  return (
    <div>
      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <div className="hero-dark">
        {/* Particle / constellation background */}
        <ParticleCanvas />

        <div className="hero-dark-inner">
          <div className="hero-pill">
            <span className="hero-pill-dot" />
            <span className="hero-pill-text">Government Scheme Registry · Karnataka</span>
          </div>

          <h1 className="hero-dark-title">
            Find the scheme<br />
            you <em>already qualify for</em>
          </h1>

          <p className="hero-dark-sub">
            Verified scholarship, subsidy, and welfare programs from authorised central and state government sources — matched to your profile instantly.
          </p>

          <div className="hero-cta-row">
            <Link to="/eligibility" className="hero-btn-primary">
              Check Eligibility
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </Link>
            <Link to="/schemes" className="hero-btn-ghost">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
              Browse Schemes
            </Link>
          </div>

          {totalSchemes > 0 && (
            <div className="hero-trust">
              <span>Privacy-first · No data stored</span>
              <span className="hero-trust-dot" />
              <span>{totalSchemes}+ verified schemes</span>
              <span className="hero-trust-dot" />
              <span>Karnataka &amp; Central Govt sources</span>
            </div>
          )}
        </div>
      </div>

      {/* ── BROWSE DIRECTORY ─────────────────────────────────────────────── */}
      <div className="dir-section-dark">
        <div style={styles.section}>
          <RevealSection>
            <h2 style={styles.sectionTitle}>Browse Directory</h2>
            <p style={styles.sectionSub}>Explore schemes categorised by official departments</p>
          </RevealSection>
          <div style={styles.catGrid}>
            {categories.map((cat) => {
              const theme = CATEGORY_THEMES[cat.name] || CATEGORY_THEMES['OTHER']
              return (
                <motion.div
                  key={cat.id}
                  whileHover={{ y: -4, boxShadow: '0 8px 28px rgba(0,0,0,0.55)' }}
                  transition={{ duration: 0.18 }}
                >
                  <Link
                    to={`/schemes?category=${encodeURIComponent(cat.name)}`}
                    style={{ ...styles.catCard, display: 'flex', flexDirection: 'column' }}
                  >
                    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: theme.color }} />
                    <div style={styles.catHeader}>
                      <div style={{ ...styles.catIconArea, background: theme.tint, color: theme.color }}>
                        {theme.icon}
                      </div>
                      <div style={styles.catName}>{cat.name}</div>
                    </div>
                    <div style={styles.catBody}>
                      <div style={styles.catCount}>{cat.scheme_count} active programs</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: theme.color }}>View →</div>
                    </div>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ── LATEST UPDATES ───────────────────────────────────────────────── */}
      {updates.length > 0 && (
        <div style={{ background: '#0E1525', borderTop: '1px solid #26304F', borderBottom: '1px solid #26304F', padding: '60px 24px' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <RevealSection>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '32px' }}>
                <div>
                  <h2 style={styles.sectionTitle}>Latest Updates</h2>
                  <p style={{ ...styles.sectionSub, marginBottom: 0 }}>System-detected changes from government portals</p>
                </div>
                <Link to="/schemes?sort=recently_updated" className="btn btn-outline" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
                  View All Updates →
                </Link>
              </div>
            </RevealSection>
            <div style={styles.updatesList}>
              {updates.map((u) => {
                const isClose = u.change_type === 'CLOSED'
                const tagStyle = {
                  ...styles.updateTag,
                  background: isClose ? 'rgba(200,80,80,0.15)' : 'rgba(107,143,113,0.15)',
                  color: isClose ? '#F09090' : '#8FBA96',
                }
                return (
                  <motion.div key={`${u.scheme?.id}-${u.detected_at}`} whileHover={{ x: 6 }} transition={{ duration: 0.18 }}>
                    <Link to={`/schemes/${u.scheme?.id}`} style={styles.updateRow}>
                      <span style={tagStyle}>{u.change_type}</span>
                      <span style={styles.updateName}>{u.scheme?.name || 'Scheme'}</span>
                      <span style={styles.updateTime}>{timeAgo(u.detected_at)}</span>
                    </Link>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── FEATURED SCHEMES (horizontal scroll) ─────────────────────────── */}
      <div style={{ ...styles.section }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <RevealSection>
            <h2 style={styles.sectionTitle}>Featured Schemes</h2>
            <p style={{ ...styles.sectionSub, marginBottom: '28px' }}>Recently verified government programs</p>
          </RevealSection>
          {loading ? (
            <div className="loading"><div className="spinner" />Loading schemes...</div>
          ) : (
            <>
              <HScrollRow schemes={schemes} />
              <div style={styles.viewAll}>
                <Link to="/schemes" className="btn btn-primary">
                  Browse All {totalSchemes || ''} Schemes →
                </Link>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── ELIGIBILITY CTA ──────────────────────────────────────────────── */}
      <div style={{ ...styles.section, paddingBottom: '100px' }}>
        <RevealSection>
          <div style={{
            background: '#182240',
            border: '1px solid #26304F',
            borderRadius: '12px',
            padding: '60px 40px',
            color: '#EDEFF5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '40px',
            boxShadow: '0 0 0 1px rgba(181,100,58,0.15), 0 16px 40px rgba(0,0,0,0.5)',
          }}>
            <div style={{ maxWidth: '500px' }}>
              <h2 style={{ fontSize: '2rem', fontFamily: "'Eczar', serif", marginBottom: '16px', color: '#EDEFF5' }}>Check Your Eligibility</h2>
              <p style={{ color: '#8890A6', fontSize: '1.1rem', marginBottom: '32px', lineHeight: 1.6 }}>
                Enter your profile details to match against structured eligibility criteria from official sources.
                <br /><br />
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#8FBA96' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  Privacy-first: No data is stored or shared.
                </span>
              </p>
              <Link to="/eligibility" className="btn btn-accent" style={{ fontSize: '1.05rem', padding: '14px 32px' }}>
                Check Eligibility Free →
              </Link>
            </div>
            <div style={{ flex: 1, minWidth: '300px', display: 'flex', justifyContent: 'center' }}>
              <div style={{
                background: '#0E1525', color: '#EDEFF5', padding: '24px', borderRadius: '12px',
                border: '1px solid #26304F',
                boxShadow: '10px 10px 0px rgba(181,100,58,0.15)',
                transform: 'rotate(2deg)',
              }}>
                <div style={{ height: '8px', width: '40px', background: 'rgba(96,145,220,0.18)', borderRadius: '4px', marginBottom: '16px' }} />
                <div style={{ fontSize: '1.2rem', fontFamily: "'Eczar', serif", fontWeight: 700, marginBottom: '8px', color: '#EDEFF5' }}>
                  Post-Matric Scholarship
                </div>
                <div style={{ height: '6px', width: '80%', background: '#26304F', borderRadius: '3px', marginBottom: '8px' }} />
                <div style={{ height: '6px', width: '60%', background: '#26304F', borderRadius: '3px', marginBottom: '24px' }} />
                <div style={{ color: '#8FBA96', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 600 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  Matched your profile
                </div>
              </div>
            </div>
          </div>
        </RevealSection>
      </div>
    </div>
  )
}

export default Home

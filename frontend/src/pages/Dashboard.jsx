import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { useAuth } from '../context/AuthContext'
import { getStats, getSchemes, getRecommendedSchemes } from '../api/api'
import '../dashboard.css'

// ── Framer-motion helpers ───────────────────────────────────────────────────
const fadeUp = {
    hidden: { opacity: 0, y: 18 },
    show: { opacity: 1, y: 0, transition: { duration: 0.52, ease: [0.22, 1, 0.36, 1] } },
}
const stagger = { show: { transition: { staggerChildren: 0.08 } } }

function RevealSection({ children, className, style }) {
    return (
        <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-80px' }}
            className={className}
            style={style}
        >
            {children}
        </motion.div>
    )
}

// ── Sidebar nav ──────────────────────────────────────────────────────────────
const SIDEBAR_ITEMS = [
    {
        id: 'dashboard', label: 'Dashboard',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>,
    },
    {
        id: 'profile', label: 'My Profile',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" /></svg>,
    },
    {
        id: 'matched', label: 'Matched Schemes',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg>,
    },
    {
        id: 'applications', label: 'Applications',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>,
    },
    {
        id: 'saved', label: 'Saved Schemes',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>,
    },
    {
        id: 'alerts', label: 'Alerts',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>,
    },
]

// ── Recharts custom tooltip ─────────────────────────────────────────────────
function CustomTooltip({ active, payload }) {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
        <div style={{ background: '#182240', border: '1px solid #26304F', borderRadius: '8px', padding: '10px 14px', fontSize: '13px', color: '#EDEFF5' }}>
            <div style={{ color: d.color, fontWeight: 700, marginBottom: '2px' }}>{d.name}</div>
            <div style={{ color: '#8890A6' }}>{d.value} schemes</div>
        </div>
    )
}

// ── Helper: build profile criteria from stored profile ──────────────────────
function buildCriteria(profile) {
    const criteria = []
    if (profile?.age) criteria.push({ label: `Age eligibility (${profile.age} years)`, met: true })
    if (profile?.income) criteria.push({ label: `Income bracket (₹${Number(profile.income).toLocaleString('en-IN')} /yr)`, met: true })
    if (profile?.caste) criteria.push({ label: `Category / caste eligibility (${profile.caste.toUpperCase()})`, met: true })
    if (profile?.education_level) criteria.push({ label: `Education level (${profile.education_level.replace(/_/g, ' ')})`, met: true })
    if (profile?.state) criteria.push({ label: `State domicile (${profile.state})`, met: true })
    if (profile?.gender) criteria.push({ label: `Gender (${profile.gender})`, met: true })
    if (criteria.length === 0) {
        criteria.push({ label: 'No profile criteria entered', met: false, hint: true })
    }
    return criteria
}

// ── Helper: derive donut data from eligibility results ──────────────────────
function buildDonut(matches) {
    if (!matches || matches.length === 0) return []
    // Group by reason keywords
    const excellent = matches.filter(m => m.match_score >= 0.85 || (m.score && m.score >= 0.85)).length
    const good = matches.filter(m => {
        const s = m.match_score ?? m.score ?? 0
        return s >= 0.65 && s < 0.85
    }).length
    const moderate = matches.filter(m => {
        const s = m.match_score ?? m.score ?? 0
        return s >= 0.4 && s < 0.65
    }).length
    const low = matches.length - excellent - good - moderate

    // Fallback: if no score field, just split roughly
    if (excellent === 0 && good === 0 && moderate === 0 && low === matches.length) {
        const total = matches.length
        return [
            { name: 'Matched Schemes', value: total, color: '#B5643A' },
        ]
    }

    const data = []
    if (excellent > 0) data.push({ name: 'Excellent Match', value: excellent, color: '#6B8F71' })
    if (good > 0) data.push({ name: 'Good Match', value: good, color: '#B5643A' })
    if (moderate > 0) data.push({ name: 'Moderate Match', value: moderate, color: '#C49A3C' })
    if (low > 0) data.push({ name: 'Low Match', value: low, color: '#5B6480' })
    return data
}

// ── Main Dashboard Component ─────────────────────────────────────────────────
export default function Dashboard() {
    const { user, signOut } = useAuth()
    const navigate = useNavigate()
    const [activeNav, setActiveNav] = useState('dashboard')
    const [totalSchemes, setTotalSchemes] = useState(null)
    const [featuredSchemes, setFeaturedSchemes] = useState([])
    const [statsLoading, setStatsLoading] = useState(true)
    const [recommendedSchemes, setRecommendedSchemes] = useState([])
    const [recommendedLoading, setRecommendedLoading] = useState(false)

    // Redirect if not signed in
    useEffect(() => {
        if (!user) navigate('/', { replace: true })
    }, [user, navigate])

    // Fetch real platform stats
    useEffect(() => {
        async function load() {
            try {
                const [statsRes, schemesRes] = await Promise.all([
                    getStats(),
                    getSchemes({ limit: 5 }),
                ])
                setTotalSchemes(statsRes.total_schemes)
                setFeaturedSchemes(schemesRes.schemes || [])
            } catch {
                // silently fail — show what we have
            } finally {
                setStatsLoading(false)
            }
        }
        load()
    }, [])

    // Fetch ML-ranked personalized recommendations
    useEffect(() => {
        if (!user?.profile) return
        async function loadRecommended() {
            setRecommendedLoading(true)
            try {
                const res = await getRecommendedSchemes(user.profile, { limit: 10 })
                setRecommendedSchemes(res.schemes || [])
            } catch {
                // silently fail
            } finally {
                setRecommendedLoading(false)
            }
        }
        loadRecommended()
    }, [user?.profile])

    if (!user) return null // will redirect

    // ── Derived data from real eligibility results ──────────────────────────
    const results = user.eligibilityResults
    const matches = results?.matches || []
    const matchCount = results?.total_matches ?? matches.length
    const criteria = buildCriteria(user.profile)
    const donutData = buildDonut(matches)
    const donutTotal = donutData.reduce((s, d) => s + d.value, 0)
    const overallPct = donutTotal > 0
        ? Math.round(((donutData.find(d => d.name === 'Excellent Match')?.value || 0) + (donutData.find(d => d.name === 'Good Match')?.value || 0)) / donutTotal * 100)
        : matchCount > 0 ? 100 : 0

    // ── Greeting ────────────────────────────────────────────────────────────
    const hour = new Date().getHours()
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
    const firstName = user.name.split(' ')[0]
    const initials = user.name.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('')

    // ── Stat cards built from real data ────────────────────────────────────
    const statCards = [
        {
            id: 'schemes-matched',
            label: 'Schemes Matched',
            value: matchCount > 0 ? String(matchCount) : '—',
            sub: matchCount > 0 ? 'Based on your profile' : 'Complete your profile to see',
            positive: matchCount > 0,
            icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg>,
            color: '#B5643A', tint: 'rgba(181,100,58,0.12)',
        },
        {
            id: 'total-schemes',
            label: 'Schemes in Database',
            value: statsLoading ? '…' : (totalSchemes ? `${totalSchemes}+` : '—'),
            sub: 'Verified government programs',
            positive: null,
            icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></svg>,
            color: '#6B8F71', tint: 'rgba(107,143,113,0.12)',
        },
        {
            id: 'profile-fields',
            label: 'Profile Fields Filled',
            value: `${criteria.filter(c => c.met).length}`,
            sub: criteria.filter(c => c.met).length === 0 ? 'Fill profile for better matches' : 'Criteria active for matching',
            positive: criteria.filter(c => c.met).length > 0,
            icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" /></svg>,
            color: '#C49A3C', tint: 'rgba(196,154,60,0.12)',
        },
        {
            id: 'match-rate',
            label: 'Match Rate',
            value: matchCount > 0 && totalSchemes ? `${Math.round((matchCount / totalSchemes) * 100)}%` : '—',
            sub: matchCount > 0 ? `${matchCount} of ${totalSchemes || '?'} schemes eligible` : 'Run eligibility check first',
            positive: null,
            icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>,
            color: '#93B8E8', tint: 'rgba(96,145,220,0.12)',
        },
    ]

    // ── No results state ────────────────────────────────────────────────────
    const hasResults = matchCount > 0
    const hasRecommended = recommendedSchemes.length > 0
    const displaySchemes = hasResults ? matches.slice(0, 5).map(m => m.scheme) : featuredSchemes.slice(0, 5)

    return (
        <div className="db-root">
            {/* ── SIDEBAR ──────────────────────────────────────────────────── */}
            <aside className="db-sidebar">
                <div className="db-sidebar-logo">
                    <div className="db-sidebar-brand-icon">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 21h18" /><path d="M3 10h18" /><path d="M5 6l7-3 7 3" />
                            <path d="M4 10v11" /><path d="M20 10v11" />
                            <path d="M8 14v3" /><path d="M12 14v3" /><path d="M16 14v3" />
                        </svg>
                    </div>
                    <span className="db-sidebar-brand-text">Suvidha</span>
                </div>

                <nav className="db-sidebar-nav">
                    {SIDEBAR_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            className={`db-sidebar-item${activeNav === item.id ? ' active' : ''}`}
                            onClick={() => setActiveNav(item.id)}
                        >
                            <span className="db-sidebar-icon">{item.icon}</span>
                            <span className="db-sidebar-label">{item.label}</span>
                            {item.id === 'matched' && matchCount > 0 && (
                                <span className="db-sidebar-badge">{matchCount}</span>
                            )}
                        </button>
                    ))}
                </nav>

                <div className="db-sidebar-footer">
                    <div className="db-avatar">{initials}</div>
                    <div className="db-sidebar-user-info">
                        <div className="db-sidebar-user-name">{user.name}</div>
                        <div className="db-sidebar-user-sub">
                            {user.profile?.state || 'All India'} · {user.profile?.education_level?.replace(/_/g, ' ') || 'Student'}
                        </div>
                    </div>
                </div>

                {/* Sign out */}
                <button
                    className="db-signout-btn"
                    onClick={() => { 
                        signOut()
                        if (window.location.origin) {
                            const domain = import.meta.env.VITE_AUTH0_DOMAIN
                            const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID
                            if (domain && clientId) {
                                window.location.href = `https://${domain}/v2/logout?client_id=${clientId}&returnTo=${encodeURIComponent(window.location.origin)}`
                                return
                            }
                        }
                        navigate('/') 
                    }}
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                        <polyline points="16 17 21 12 16 7" />
                        <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Sign out
                </button>
            </aside>

            {/* ── MAIN ─────────────────────────────────────────────────────── */}
            <main className="db-main">

                {/* Header */}
                <motion.div
                    className="db-topbar"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                >
                    <div className="db-topbar-left">
                        <h1 className="db-greeting">{greeting}, {firstName}</h1>
                        <p className="db-greeting-sub">
                            {hasResults
                                ? `Here's your scheme match summary — ${matchCount} schemes matched to your profile`
                                : 'Complete your profile to see personalised matches and eligibility results'}
                        </p>
                    </div>
                    <div className="db-topbar-right">
                        <div className="db-search-bar">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#5B6480', flexShrink: 0 }}>
                                <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                            </svg>
                            <input type="text" placeholder="Search schemes…" className="db-search-input" />
                        </div>
                        <div className="db-avatar db-avatar-lg">{initials}</div>
                    </div>
                </motion.div>

                {/* Stat cards */}
                <motion.div className="db-stat-grid" variants={stagger} initial="hidden" animate="show">
                    {statCards.map((card) => (
                        <motion.div key={card.id} variants={fadeUp}>
                            <motion.div
                                className="db-stat-card"
                                whileHover={{ y: -4, boxShadow: '0 8px 28px rgba(0,0,0,0.55)' }}
                                transition={{ duration: 0.18 }}
                            >
                                <div className="db-stat-icon" style={{ background: card.tint, color: card.color }}>
                                    {card.icon}
                                </div>
                                <div className="db-stat-body">
                                    <div className="db-stat-value">{card.value}</div>
                                    <div className="db-stat-label">{card.label}</div>
                                    <div className="db-stat-sub" style={{
                                        color: card.positive === true ? '#6B8F71'
                                            : card.positive === false ? '#F87171'
                                                : '#8890A6'
                                    }}>{card.sub}</div>
                                </div>
                            </motion.div>
                        </motion.div>
                    ))}
                </motion.div>

                {/* No-results CTA banner */}
                {!hasResults && (
                    <RevealSection>
                        <div className="db-no-results-banner">
                            <div className="db-no-results-icon">🎯</div>
                            <div className="db-no-results-body">
                                <div className="db-no-results-title">No eligibility results yet</div>
                                <div className="db-no-results-sub">
                                    Run the eligibility checker to get personalised scheme matches based on your profile.
                                </div>
                            </div>
                            <Link to="/eligibility" className="db-no-results-btn">
                                Check Eligibility →
                            </Link>
                        </div>
                    </RevealSection>
                )}

                {/* Middle row: Donut + Criteria */}
                <div className="db-mid-row" style={{ marginBottom: '24px' }}>

                    {/* Donut */}
                    <RevealSection className="db-panel db-donut-panel">
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">Match Overview</h2>
                                <span className="db-panel-sub">Eligibility breakdown by match quality</span>
                            </div>
                        </div>
                        {donutData.length > 0 ? (
                            <div className="db-donut-wrap">
                                <div className="db-donut-chart">
                                    <ResponsiveContainer width="100%" height={220}>
                                        <PieChart>
                                            <Pie data={donutData} cx="50%" cy="50%" innerRadius={68} outerRadius={98} paddingAngle={3} dataKey="value" strokeWidth={0}>
                                                {donutData.map((entry) => (
                                                    <Cell key={entry.name} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<CustomTooltip />} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="db-donut-center">
                                        <div className="db-donut-pct">{overallPct}%</div>
                                        <div className="db-donut-pct-label">eligible</div>
                                    </div>
                                </div>
                                <div className="db-donut-legend">
                                    {donutData.map((d) => (
                                        <div key={d.name} className="db-legend-row">
                                            <span className="db-legend-dot" style={{ background: d.color }} />
                                            <span className="db-legend-name">{d.name}</span>
                                            <span className="db-legend-count">{d.value} schemes</span>
                                        </div>
                                    ))}
                                    <div className="db-legend-total">
                                        <span>Total matched</span>
                                        <span style={{ color: '#EDEFF5', fontWeight: 700 }}>{donutTotal} schemes</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="db-panel-empty">
                                <div className="db-panel-empty-icon">📊</div>
                                <div>Run Eligibility Check to see your match breakdown</div>
                                <Link to="/eligibility" className="db-criteria-cta" style={{ marginTop: '12px', display: 'inline-block' }}>
                                    Check Eligibility →
                                </Link>
                            </div>
                        )}
                    </RevealSection>

                    {/* Criteria checklist */}
                    <RevealSection className="db-panel db-criteria-panel">
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">Your Profile Criteria</h2>
                                <span className="db-panel-sub">Fields used for scheme matching</span>
                            </div>
                        </div>
                        <div className="db-criteria-list">
                            {criteria.map((c) => (
                                <div key={c.label} className={`db-criteria-row${c.met ? ' met' : ' unmet'}`}>
                                    <div className="db-criteria-icon">
                                        {c.met ? (
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B8F71" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        ) : (
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5B6480" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <circle cx="12" cy="12" r="10" />
                                                <path d="M12 8v4M12 16h.01" />
                                            </svg>
                                        )}
                                    </div>
                                    <span className="db-criteria-label">{c.label}</span>
                                    <span className="db-criteria-status">{c.met ? 'Set' : 'Not set'}</span>
                                </div>
                            ))}
                        </div>
                        <Link to="/eligibility" className="db-criteria-cta">
                            Update profile & re-check →
                        </Link>
                    </RevealSection>
                </div>

                {/* ML-Personalized Recommendations */}
                {hasRecommended && (
                    <RevealSection className="db-panel" style={{ marginBottom: '24px' }}>
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">
                                    <span style={{ marginRight: '8px' }}>🤖</span>
                                    Recommended for You
                                </h2>
                                <span className="db-panel-sub">
                                    Personalised by ML · {recommendedSchemes.length} schemes ranked by relevance to your profile
                                </span>
                            </div>
                        </div>

                        <div className="db-schemes-list">
                            {recommendedSchemes.map((scheme, i) => {
                                const relevancePct = scheme.relevance_score
                                    ? Math.round(scheme.relevance_score * 100)
                                    : null
                                const matchColor =
                                    relevancePct >= 80 ? '#6B8F71'
                                    : relevancePct >= 60 ? '#B5643A'
                                    : relevancePct >= 40 ? '#C49A3C'
                                    : '#5B6480'
                                return (
                                    <motion.div
                                        key={scheme?.id ?? i}
                                        className="db-scheme-row"
                                        whileHover={{ x: 4, backgroundColor: 'rgba(38,48,79,0.5)' }}
                                        transition={{ duration: 0.15 }}
                                    >
                                        <div className="db-scheme-rank">
                                            <span style={{ fontSize: '14px', fontWeight: 700 }}>{String(i + 1).padStart(2, '0')}</span>
                                        </div>
                                        <div className="db-scheme-info">
                                            <div className="db-scheme-name">{scheme?.name || 'Unknown Scheme'}</div>
                                            <div className="db-scheme-dept">{scheme?.provider_name || scheme?.source || ''}</div>
                                        </div>
                                        <div className="db-scheme-meta">
                                            {scheme?.category_name && (
                                                <span className="db-scheme-tag" style={{ color: '#B5643A', background: 'rgba(181,100,58,0.12)' }}>
                                                    {scheme.category_name}
                                                </span>
                                            )}
                                            {scheme?.state_code && (
                                                <span className="db-scheme-tag" style={{ color: '#5eead4', background: 'rgba(45,212,191,0.12)' }}>
                                                    {scheme.state_code === 'IN' ? 'All India' : scheme.state_code}
                                                </span>
                                            )}
                                            {relevancePct !== null && (
                                                <span
                                                    className="db-scheme-tag"
                                                    style={{
                                                        color: matchColor,
                                                        background: `${matchColor}18`,
                                                        fontWeight: 700,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '4px',
                                                    }}
                                                >
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                                                    </svg>
                                                    {relevancePct}% match
                                                </span>
                                            )}
                                            {scheme?.match_details?.match_ratio != null && (
                                                <span style={{ fontSize: '11px', color: '#8890A6' }}>
                                                    {Math.round(scheme.match_details.match_ratio * 100)}% criteria met
                                                </span>
                                            )}
                                            <Link to={`/schemes/${scheme?.id}`} className="db-scheme-view-btn">View →</Link>
                                        </div>
                                    </motion.div>
                                )
                            })}
                        </div>
                    </RevealSection>
                )}

                {recommendedLoading && (
                    <RevealSection className="db-panel" style={{ marginBottom: '24px' }}>
                        <div className="db-panel-empty">
                            <span className="signin-spinner" style={{ width: '20px', height: '20px', border: '2.5px solid rgba(181,100,58,0.3)', borderTopColor: '#B5643A' }} />
                            <div style={{ marginTop: '8px', color: '#8890A6', fontSize: '13px' }}>Loading personalised recommendations…</div>
                        </div>
                    </RevealSection>
                )}

                {/* Matched / Featured schemes */}
                <RevealSection className="db-panel" style={{ marginBottom: '40px' }}>
                    <div className="db-panel-header">
                        <div>
                            <h2 className="db-panel-title">
                                {hasResults ? 'Your Matched Schemes' : 'Browse All Schemes'}
                            </h2>
                            <span className="db-panel-sub">
                                {hasResults
                                    ? `Top ${Math.min(5, displaySchemes.length)} results from your eligibility check`
                                    : 'Sign up and run an eligibility check to see personalised matches'}
                            </span>
                        </div>
                        <Link to={hasResults ? '/eligibility' : '/schemes'} className="db-panel-link">
                            {hasResults ? 'Re-run check →' : 'View all →'}
                        </Link>
                    </div>

                    {displaySchemes.length > 0 ? (
                        <div className="db-schemes-list">
                            {displaySchemes.map((scheme, i) => (
                                <motion.div
                                    key={scheme?.id ?? i}
                                    className="db-scheme-row"
                                    whileHover={{ x: 4, backgroundColor: 'rgba(38,48,79,0.5)' }}
                                    transition={{ duration: 0.15 }}
                                >
                                    <div className="db-scheme-rank">{String(i + 1).padStart(2, '0')}</div>
                                    <div className="db-scheme-info">
                                        <div className="db-scheme-name">{scheme?.name || 'Unknown Scheme'}</div>
                                        <div className="db-scheme-dept">{scheme?.department || scheme?.source || ''}</div>
                                    </div>
                                    <div className="db-scheme-meta">
                                        {scheme?.category && (
                                            <span className="db-scheme-tag" style={{ color: '#B5643A', background: 'rgba(181,100,58,0.12)' }}>
                                                {scheme.category}
                                            </span>
                                        )}
                                        {scheme?.benefit_amount && (
                                            <span className="db-scheme-amount">{scheme.benefit_amount}</span>
                                        )}
                                        {hasResults && matches[i]?.match_reason && (
                                            <span style={{ fontSize: '12px', color: '#6B8F71', maxWidth: '200px', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                                                ✓ {matches[i].match_reason}
                                            </span>
                                        )}
                                        <Link to={`/schemes/${scheme?.id}`} className="db-scheme-view-btn">View →</Link>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <div className="db-panel-empty">
                            <div className="db-panel-empty-icon">📋</div>
                            <div>No schemes to display yet.</div>
                            <Link to="/eligibility" className="db-criteria-cta" style={{ marginTop: '12px', display: 'inline-block' }}>
                                Check Eligibility →
                            </Link>
                        </div>
                    )}
                </RevealSection>

            </main>
        </div>
    )
}

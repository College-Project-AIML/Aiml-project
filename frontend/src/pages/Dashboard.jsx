import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { useAuth } from '../context/AuthContext'
import { getStats, getSchemes, getRecommendedSchemes, getUpdates } from '../api/api'
import { getApplications, removeApplication, updateApplicationProgress } from '../utils/applicationTracker'
import { timeAgo } from '../utils'
import SuvidhaMark from '../components/SuvidhaMark'
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
            <div style={{ color: '#8890A6' }}>Category in your matches</div>
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

// ── Helper: group the user's matches by their scheme category ───────────────
function buildDonut(matches) {
    if (!matches?.length) return []

    const categoryCounts = new Map()
    matches.forEach((match) => {
        const scheme = match.scheme || match
        const category = scheme?.category_name?.trim() || 'Other support'
        categoryCounts.set(category, (categoryCounts.get(category) || 0) + 1)
    })

    const categories = [...categoryCounts.entries()]
        .sort(([, firstCount], [, secondCount]) => secondCount - firstCount)
    const mainCategories = categories.slice(0, 4)
    const remainingCount = categories.slice(4).reduce((sum, [, count]) => sum + count, 0)
    const palette = ['#B5643A', '#6B8F71', '#93B8E8', '#C49A3C', '#7667B9']
    const data = mainCategories.map(([name, value], index) => ({ name, value, color: palette[index] }))

    if (remainingCount > 0) {
        data.push({ name: 'Other support', value: remainingCount, color: palette[4] })
    }

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
    const [applications, setApplications] = useState([])
    const [schemeUpdates, setSchemeUpdates] = useState([])
    const [alertsLoading, setAlertsLoading] = useState(false)
    const [alertFilter, setAlertFilter] = useState('all')
    const [readAlertIds, setReadAlertIds] = useState(() => {
        try { return JSON.parse(localStorage.getItem('suvidha-read-alerts')) || [] } catch { return [] }
    })

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

    useEffect(() => {
        if (user) setApplications(getApplications(user.user_id || user.email))
    }, [user])

    useEffect(() => {
        if (activeNav !== 'alerts' || !user) return
        async function loadAlerts() {
            setAlertsLoading(true)
            try {
                const response = await getUpdates({ limit: 50 })
                setSchemeUpdates(response.updates || [])
            } catch {
                setSchemeUpdates([])
            } finally {
                setAlertsLoading(false)
            }
        }
        loadAlerts()
    }, [activeNav, user])

    if (!user) return null // will redirect

    // ── Derived data from real eligibility results ──────────────────────────
    const results = user.eligibilityResults
    const matches = results?.matches || []
    const matchCount = results?.total_matches ?? matches.length
    const criteria = buildCriteria(user.profile)
    const donutData = buildDonut(matches)

    // ── Greeting ────────────────────────────────────────────────────────────
    const hour = new Date().getHours()
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
    const firstName = user.name.split(' ')[0]
    const initials = user.name.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('')
    const profileValues = [
        { label: 'Full name', value: user.name },
        { label: 'Age', value: user.profile?.age ? `${user.profile.age} years` : 'Not set' },
        { label: 'Annual income', value: user.profile?.income ? `₹${Number(user.profile.income).toLocaleString('en-IN')} / year` : 'Not set' },
        { label: 'Gender', value: user.profile?.gender ? user.profile.gender.charAt(0).toUpperCase() + user.profile.gender.slice(1) : 'Not set' },
        { label: 'Category', value: user.profile?.caste ? user.profile.caste.toUpperCase() : 'Not set' },
        { label: 'State', value: user.profile?.state || 'Not set' },
        { label: 'Education level', value: user.profile?.education_level ? user.profile.education_level.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()) : 'Not set' },
    ]
    const progressLabels = {
        INTERESTED: 'Interested',
        APPLIED: 'Applied on official portal',
        SUBMITTED: 'Submitted',
        APPROVED: 'Approved',
        REJECTED: 'Rejected',
    }

    const handleProgressChange = (applicationId, progress) => {
        updateApplicationProgress(applicationId, progress)
        setApplications(getApplications(user.user_id || user.email))
    }
    const handleCompleteApplication = (applicationId) => {
        removeApplication(applicationId)
        setApplications(getApplications(user.user_id || user.email))
    }
    const markAlertRead = (alertId) => {
        const next = [...new Set([...readAlertIds, alertId])]
        setReadAlertIds(next)
        localStorage.setItem('suvidha-read-alerts', JSON.stringify(next))
    }
    const trackedSchemeIds = new Set(applications.map((application) => application.scheme.id))
    const applicationAlerts = applications.flatMap((application) => {
        const alerts = []
        if (application.progress === 'INTERESTED') {
            alerts.push({ id: `review-${application.id}`, type: 'application', title: 'Action needed: review your application', text: `Review required documents for ${application.scheme.name}.`, scheme: application.scheme })
        }
        if (application.scheme.status === 'INACTIVE') {
            alerts.push({ id: `inactive-${application.id}`, type: 'application', title: 'Tracked scheme is inactive', text: `${application.scheme.name} is currently marked inactive. Verify availability on the official portal.`, scheme: application.scheme })
        }
        return alerts
    })
    const updateAlerts = schemeUpdates
        .filter((update) => trackedSchemeIds.has(update.scheme?.id))
        .map((update) => ({
            id: `update-${update.scheme?.id}-${update.detected_at}`,
            type: 'scheme',
            title: update.change_type === 'CLOSED' ? 'Scheme closed' : update.change_type === 'NEW' ? 'New scheme update' : 'Tracked scheme updated',
            text: `${update.scheme?.name || 'A tracked scheme'} was marked ${update.change_type.toLowerCase()}.`,
            scheme: update.scheme,
            detectedAt: update.detected_at,
        }))
    const allAlerts = [...applicationAlerts, ...updateAlerts]
    const visibleAlerts = allAlerts.filter((alert) => alertFilter === 'all' || alert.type === alertFilter)

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
                        <SuvidhaMark size={34} />
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

                {activeNav === 'profile' && (
                    <RevealSection className="db-panel db-profile-panel" style={{ marginBottom: '40px' }}>
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">My Profile</h2>
                                <span className="db-panel-sub">Details used to personalise your scheme recommendations</span>
                            </div>
                            <Link to="/onboarding" className="db-criteria-cta">Update Profile →</Link>
                        </div>
                        <div className="db-profile-grid">
                            {profileValues.map((field) => (
                                <div className="db-profile-field" key={field.label}>
                                    <span className="db-profile-label">{field.label}</span>
                                    <span className={`db-profile-value${field.value === 'Not set' ? ' empty' : ''}`}>{field.value}</span>
                                </div>
                            ))}
                        </div>
                    </RevealSection>
                )}

                {activeNav === 'applications' && (
                    <RevealSection className="db-panel db-applications-panel" style={{ marginBottom: '40px' }}>
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">My Applications</h2>
                                <span className="db-panel-sub">Schemes you chose to track in Suvidha</span>
                            </div>
                        </div>
                        {applications.length === 0 ? (
                            <div className="db-panel-empty">
                                <div className="db-panel-empty-icon">📋</div>
                                <div>No tracked applications yet.</div>
                                <Link to="/schemes" className="db-criteria-cta" style={{ marginTop: '12px', display: 'inline-block' }}>Browse Schemes →</Link>
                            </div>
                        ) : (
                            <div className="db-application-list">
                                {applications.map((application) => {
                                    const trackedScheme = application.scheme
                                    const documents = trackedScheme.documents_required || []
                                    return (
                                        <div className="db-application-card" key={application.id}>
                                            <div className="db-application-header">
                                                <div>
                                                    <h3 className="db-application-name">{trackedScheme.name}</h3>
                                                    <div className="db-application-tags">
                                                        <span className={`db-application-status ${trackedScheme.status === 'ACTIVE' ? 'active' : 'inactive'}`}>{trackedScheme.status || 'UNKNOWN'}</span>
                                                        {trackedScheme.category_name && <span className="db-scheme-tag">{trackedScheme.category_name}</span>}
                                                    </div>
                                                </div>
                                                <select value={application.progress} onChange={(event) => handleProgressChange(application.id, event.target.value)} className="db-application-progress">
                                                    {Object.entries(progressLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
                                                </select>
                                            </div>
                                            <div className="db-application-details">
                                                <div><span>Last date to apply</span><strong>{trackedScheme.application_deadline || 'Not published in our source'}</strong></div>
                                                <div><span>Required documents</span><strong>{documents.length ? `${documents.length} listed` : 'Not listed'}</strong></div>
                                            </div>
                                            {documents.length > 0 && (
                                                <ul className="db-application-documents">
                                                    {documents.map((document, index) => <li key={index}>{document.document_name}{!document.is_mandatory ? ' (optional)' : ''}</li>)}
                                                </ul>
                                            )}
                                            <div className="db-application-actions">
                                                <Link to={`/schemes/${trackedScheme.id}`} className="db-scheme-view-btn">View scheme details →</Link>
                                                {trackedScheme.link && <a href={trackedScheme.link} target="_blank" rel="noreferrer" className="db-scheme-view-btn">Official portal ↗</a>}
                                                <button type="button" onClick={() => handleCompleteApplication(application.id)} className="db-scheme-view-btn db-application-complete-btn">Mark done &amp; remove ✓</button>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </RevealSection>
                )}

                {activeNav === 'alerts' && (
                    <RevealSection className="db-panel db-alerts-panel" style={{ marginBottom: '40px' }}>
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">Alerts</h2>
                                <span className="db-panel-sub">Updates and reminders for schemes you are tracking</span>
                            </div>
                        </div>
                        <div className="db-alert-filters">
                            {[['all', 'All'], ['application', 'Applications'], ['scheme', 'Scheme updates']].map(([value, label]) => (
                                <button key={value} onClick={() => setAlertFilter(value)} className={`db-alert-filter${alertFilter === value ? ' active' : ''}`}>{label}</button>
                            ))}
                        </div>
                        {alertsLoading ? (
                            <div className="db-panel-empty">Loading updates…</div>
                        ) : visibleAlerts.length === 0 ? (
                            <div className="db-panel-empty">
                                <div className="db-panel-empty-icon">🔔</div>
                                <div>No alerts yet.</div>
                                <div style={{ marginTop: '6px', fontSize: '13px' }}>Track a scheme to receive application reminders and scheme updates.</div>
                            </div>
                        ) : (
                            <div className="db-alert-list">
                                {visibleAlerts.map((alert) => {
                                    const isRead = readAlertIds.includes(alert.id)
                                    return (
                                        <div className={`db-alert-card${isRead ? ' read' : ''}`} key={alert.id}>
                                            <div className="db-alert-dot" />
                                            <div className="db-alert-content">
                                                <div className="db-alert-title">{alert.title}</div>
                                                <div className="db-alert-text">{alert.text}</div>
                                                {alert.detectedAt && <div className="db-alert-time">{timeAgo(alert.detectedAt)}</div>}
                                                <div className="db-alert-actions">
                                                    <Link to={`/schemes/${alert.scheme?.id}`} className="db-scheme-view-btn">View scheme →</Link>
                                                    {!isRead && <button onClick={() => markAlertRead(alert.id)} className="db-alert-read-btn">Mark read</button>}
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </RevealSection>
                )}

                {activeNav === 'matched' && (
                    <RevealSection className="db-panel db-matched-panel" style={{ marginBottom: '40px' }}>
                        <div className="db-panel-header">
                            <div>
                                <h2 className="db-panel-title">Your Matched Schemes</h2>
                                <span className="db-panel-sub">
                                    {matchCount > 0
                                        ? `${matchCount} schemes matched to your profile — explore the ones that suit you.`
                                        : 'Complete your profile and run an eligibility check to see your matches.'}
                                </span>
                            </div>
                            {matchCount > 0 && <span className="db-matched-count">{matchCount} matches</span>}
                        </div>
                        {matches.length === 0 ? (
                            <div className="db-panel-empty">
                                <div className="db-panel-empty-icon">🎯</div>
                                <div>No matched schemes yet.</div>
                                <Link to="/eligibility" className="db-criteria-cta" style={{ marginTop: '12px', display: 'inline-block' }}>Check Eligibility →</Link>
                            </div>
                        ) : (
                            <div className="db-matched-grid">
                                {matches.map((match, index) => {
                                    const matchedScheme = match.scheme || match
                                    return (
                                        <motion.div key={matchedScheme?.id || index} className="db-matched-card" whileHover={{ y: -4 }} transition={{ duration: 0.18 }}>
                                            <div className="db-matched-card-top">
                                                <span className="db-matched-rank">#{String(index + 1).padStart(2, '0')}</span>
                                                <span className={`db-application-status ${matchedScheme?.status === 'ACTIVE' ? 'active' : 'inactive'}`}>{matchedScheme?.status || 'ACTIVE'}</span>
                                            </div>
                                            <h3>{matchedScheme?.name || 'Scheme'}</h3>
                                            <p>{matchedScheme?.description || 'View the full scheme details to learn more.'}</p>
                                            <div className="db-matched-tags">
                                                {matchedScheme?.category_name && <span className="db-scheme-tag">{matchedScheme.category_name}</span>}
                                                <span className="db-scheme-tag">{matchedScheme?.state_code || 'All India'}</span>
                                            </div>
                                            {match.match_reason && <div className="db-matched-reason">✓ {match.match_reason}</div>}
                                            <Link to={`/schemes/${matchedScheme?.id}`} className="db-matched-view">Explore scheme →</Link>
                                        </motion.div>
                                    )
                                })}
                            </div>
                        )}
                    </RevealSection>
                )}

                {!['profile', 'applications', 'alerts', 'matched'].includes(activeNav) && <>
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
                                <h2 className="db-panel-title">Discover Your Benefits</h2>
                                <span className="db-panel-sub">The support areas most relevant to your profile.</span>
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
                                        <div className="db-donut-pct-label">scheme categories</div>
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
                                    Recommended for You
                                </h2>
                                <span className="db-panel-sub">
                                    Ranked by model relevance · {recommendedSchemes.length} schemes matched to your profile
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
                </>}

            </main>
        </div>
    )
}

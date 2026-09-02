import { useEffect, useState } from 'react'
import { Routes, Route, Link, NavLink, useLocation, Navigate, useNavigate } from 'react-router-dom'
import Home from './pages/Home'
import Schemes from './pages/Schemes'
import SchemeDetail from './pages/SchemeDetail'
import Eligibility from './pages/Eligibility'
import About from './pages/About'
import Dashboard from './pages/Dashboard'
import ChatbotWidget from './components/ChatbotWidget'
import SignInModal from './components/SignInModal'
import Onboarding from './pages/Onboarding'
import { useAuth } from './context/AuthContext'
import { useAuth0 } from '@auth0/auth0-react'

// ── Protected route — redirects to home if not signed in ────────────────────
function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/" replace />
  return children
}

// ── Protected route — redirects to onboarding if profile is missing ───────────
function RequireOnboarding({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/" replace />
  if (user.profile === null || user.profile === undefined) {
    return <Navigate to="/onboarding" replace />
  }
  return children
}

// ── Auth0 Callback Handler (only renders if Auth0 is configured) ────────────
function Auth0CallbackHandler() {
  const { isAuthenticated, user: auth0User } = useAuth0()
  const { loginWithAuth0User, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated && auth0User && !user) {
      loginWithAuth0User(auth0User)
      navigate('/onboarding')
    }
  }, [isAuthenticated, auth0User, user, loginWithAuth0User, navigate])
  
  return null
}

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, signOut } = useAuth()
  const [showSignIn, setShowSignIn] = useState(false)
  const [navScrolled, setNavScrolled] = useState(false)

  const isDashboard = location.pathname.startsWith('/dashboard')

  // If a non-signed-in user tries to go to /dashboard, show sign-in modal
  const handleDashboardClick = (e) => {
    if (!user) {
      e.preventDefault()
      setShowSignIn(true)
    }
  }

  // Lock permanently to dark mode
  useEffect(() => {
    document.documentElement.dataset.theme = 'dark'
    localStorage.removeItem('suvidha-theme')
  }, [])

  // Transparent navbar — becomes glassy on scroll
  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return 'active'
    if (path !== '/' && location.pathname.startsWith(path)) return 'active'
    return ''
  }

  // Derive initials for avatar button
  const initials = user?.name
    ?.trim()
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || ''

  return (
    <>
      {import.meta.env.VITE_AUTH0_DOMAIN && import.meta.env.VITE_AUTH0_CLIENT_ID && <Auth0CallbackHandler />}
      {/* ── Global navbar (hidden on /dashboard which has its own sidebar) */}
      {!isDashboard && (
        <nav className={`navbar${navScrolled ? ' scrolled' : ''}`}>
          <div className="navbar-inner">
            <Link to="/" className="navbar-brand">
              <div className="brand-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 21h18" /><path d="M3 10h18" /><path d="M5 6l7-3 7 3" />
                  <path d="M4 10v11" /><path d="M20 10v11" />
                  <path d="M8 14v3" /><path d="M12 14v3" /><path d="M16 14v3" />
                </svg>
              </div>
              Suvidha
            </Link>

            <div className="navbar-right">
              <div className="navbar-links">
                <Link to="/" className={isActive('/')}>Home</Link>
                <Link to="/schemes" className={isActive('/schemes')}>Schemes</Link>
                <Link to="/eligibility" className={isActive('/eligibility')}>Check Eligibility</Link>
                <Link to="/dashboard" className={isActive('/dashboard')} onClick={handleDashboardClick}>Dashboard</Link>
                <Link to="/about" className={isActive('/about')}>About</Link>
              </div>

              {user ? (
                /* Signed-in state: show name + sign-out */
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Link
                    to="/dashboard"
                    style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      background: 'rgba(181,100,58,0.1)', border: '1px solid rgba(181,100,58,0.3)',
                      borderRadius: '100px', padding: '4px 12px 4px 4px',
                      textDecoration: 'none', color: '#EDEFF5', transition: 'background 0.2s',
                    }}
                    className="navbar-user-pill"
                  >
                    <div style={{
                      width: '26px', height: '26px', borderRadius: '50%',
                      background: 'linear-gradient(135deg,#B5643A,#9e5430)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '10px', fontWeight: 700, color: '#fff', flexShrink: 0,
                    }}>
                      {initials}
                    </div>
                    <span style={{ fontSize: '13px', fontFamily: "'DM Sans', sans-serif", fontWeight: 500 }}>
                      {user.name.split(' ')[0]}
                    </span>
                  </Link>
                  <button
                    className="navbar-signin"
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
                    }}
                    style={{ fontSize: '12px' }}
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                /* Signed-out state */
                <>
                  <button
                    className="navbar-signin"
                    onClick={() => setShowSignIn(true)}
                    id="navbar-signin-btn"
                  >
                    Sign in
                  </button>
                  <Link to="/eligibility" className="navbar-cta">Check Eligibility</Link>
                </>
              )}
            </div>
          </div>
        </nav>
      )}

      {/* ── Page content */}
      <div className={isDashboard ? '' : 'page'}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/schemes" element={<Schemes />} />
          <Route path="/schemes/:id" element={<SchemeDetail />} />
          <Route path="/eligibility" element={<Eligibility />} />
          <Route path="/about" element={<About />} />
          <Route
            path="/onboarding"
            element={
              <RequireAuth>
                <Onboarding />
              </RequireAuth>
            }
          />
          <Route
            path="/dashboard"
            element={
              <RequireOnboarding>
                <Dashboard />
              </RequireOnboarding>
            }
          />
        </Routes>
      </div>

      {/* ── Footer (hidden on dashboard) */}
      {!isDashboard && (
        <footer className="footer">
          Aiml-project — Government Schemes Discovery Platform · Built for learning &amp; portfolio
        </footer>
      )}

      {/* ── Sign-in modal */}
      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      <ChatbotWidget />
    </>
  )
}

export default App

import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Schemes from './pages/Schemes'
import SchemeDetail from './pages/SchemeDetail'
import Eligibility from './pages/Eligibility'
import About from './pages/About'
import ChatbotWidget from './components/ChatbotWidget'

function App() {
  const location = useLocation()

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return 'active'
    if (path !== '/' && location.pathname.startsWith(path)) return 'active'
    return ''
  }

  return (
    <>
      <nav className="navbar">
        <div className="navbar-inner">
          <Link to="/" className="navbar-brand">
            <div className="brand-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18"></path><path d="M3 10h18"></path><path d="M5 6l7-3 7 3"></path><path d="M4 10v11"></path><path d="M20 10v11"></path><path d="M8 14v3"></path><path d="M12 14v3"></path><path d="M16 14v3"></path></svg>
            </div>
            Suvidha
          </Link>
          <div className="navbar-right">
            <div className="navbar-links">
              <Link to="/" className={isActive('/')}>Home</Link>
              <Link to="/schemes" className={isActive('/schemes')}>Schemes</Link>
              <Link to="/eligibility" className={isActive('/eligibility')}>Check Eligibility</Link>
              <Link to="/about" className={isActive('/about')}>About</Link>
            </div>
            <button className="navbar-signin">Sign in</button>
          </div>
        </div>
      </nav>

      <div className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/schemes" element={<Schemes />} />
          <Route path="/schemes/:id" element={<SchemeDetail />} />
          <Route path="/eligibility" element={<Eligibility />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>

      <footer className="footer">
        Aiml-project — Government Schemes Discovery Platform · Built for learning & portfolio
      </footer>
      <ChatbotWidget />
    </>
  )
}

export default App

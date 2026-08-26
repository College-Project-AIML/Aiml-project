import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Schemes from './pages/Schemes'
import SchemeDetail from './pages/SchemeDetail'
import Eligibility from './pages/Eligibility'
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
            <span className="brand-icon">🏛</span>
            Suvidha
          </Link>
          <div className="navbar-links">
            <Link to="/" className={isActive('/')}>Home</Link>
            <Link to="/schemes" className={isActive('/schemes')}>Schemes</Link>
            <Link to="/eligibility" className={isActive('/eligibility')}>Check Eligibility</Link>
          </div>
        </div>
      </nav>

      <div className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/schemes" element={<Schemes />} />
          <Route path="/schemes/:id" element={<SchemeDetail />} />
          <Route path="/eligibility" element={<Eligibility />} />
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

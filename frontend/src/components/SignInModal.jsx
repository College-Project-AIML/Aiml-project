import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence, useSpring } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useAuth0 } from '@auth0/auth0-react'
import SuvidhaMark from './SuvidhaMark'
import '../signin.css'

// Gradient palettes derived from the brand colour family
const AVATAR_GRADIENTS = [
    ['#B5643A', '#8f4a28'],
    ['#3A9BB5', '#2c7488'],
    ['#8A5AB5', '#6a3f94'],
    ['#B58A3A', '#8f6b28'],
    ['#3AB58A', '#2c8a68'],
]

const hashString = (str) => {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
        hash = (hash * 31 + str.charCodeAt(i)) | 0
    }
    return Math.abs(hash)
}

// Staggered entrance used by the form sections
const fadeUp = {
    hidden: { opacity: 0, y: 12 },
    show: (i) => ({
        opacity: 1,
        y: 0,
        transition: { delay: 0.06 * i, duration: 0.35, ease: [0.22, 1, 0.36, 1] },
    }),
}

export default function SignInModal({ onClose }) {
    const { signIn } = useAuth()
    const navigate = useNavigate()

    // Auth0 hook (will throw if Auth0Provider is not wrapping the app, but we only call it if env vars exist)
    const { loginWithRedirect } = useAuth0() || {}

    const [name, setName] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // ── Subtle 3D tilt that follows the cursor ──
    const modalRef = useRef(null)
    const rotateX = useSpring(0, { stiffness: 160, damping: 22 })
    const rotateY = useSpring(0, { stiffness: 160, damping: 22 })

    const handleTilt = (e) => {
        const el = modalRef.current
        if (!el || e.pointerType !== 'mouse') return
        const rect = el.getBoundingClientRect()
        const px = (e.clientX - rect.left) / rect.width - 0.5
        const py = (e.clientY - rect.top) / rect.height - 0.5
        rotateX.set(-py * 5)
        rotateY.set(px * 5)
    }

    const resetTilt = () => {
        rotateX.set(0)
        rotateY.set(0)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!name.trim()) { setError('Please enter your name'); return }
        setError('')
        setLoading(true)
        // Brief pause so the loading state is felt
        await new Promise((r) => setTimeout(r, 550))
        signIn({ name: name.trim(), profile: null, eligibilityResults: null })
        onClose()
        navigate('/onboarding')
    }

    const handleAuth0Login = async () => {
        try {
            const domain = import.meta.env.VITE_AUTH0_DOMAIN
            const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID
            if (domain && clientId && loginWithRedirect) {
                await loginWithRedirect({
                    appState: { returnTo: '/onboarding' }
                })
                return
            }
            setError('Auth0 is not configured. Please set VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID in frontend/.env')
        } catch (err) {
            console.error(err)
            setError('Auth0 sign-in error. Please check your Auth0 settings.')
        }
    }

    const trimmed = name.trim()
    const initials = trimmed
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0].toUpperCase())
        .join('')
    const firstName = trimmed.split(' ')[0] || ''
    const [avatarFrom, avatarTo] = AVATAR_GRADIENTS[hashString(trimmed || 'guest') % AVATAR_GRADIENTS.length]

    return (
        <AnimatePresence>
            {/* Backdrop wraps the modal so flexbox centering works */}
            <motion.div
                className="signin-backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
            >
                {/* Ambient glow orbs */}
                <div className="signin-orb signin-orb-1" />
                <div className="signin-orb signin-orb-2" />
                <div className="signin-orb signin-orb-3" />
                <div className="signin-modal-glow" />

                {/* Modal */}
                <motion.div
                    ref={modalRef}
                    className="signin-modal"
                    initial={{ opacity: 0, y: 24, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 16, scale: 0.95 }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                    style={{ rotateX, rotateY, transformPerspective: 1000 }}
                    onMouseMove={handleTilt}
                    onMouseLeave={resetTilt}
                    role="dialog"
                    aria-modal="true"
                    aria-label="Sign in to Suvidha"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="signin-modal-header">
                        <div className="signin-brand">
                            <div className="signin-brand-icon">
                                <SuvidhaMark size={30} />
                            </div>
                            <span className="signin-brand-name">Suvidha</span>
                        </div>
                        <button className="signin-close" onClick={onClose} aria-label="Close">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} noValidate>
                        <div style={{ padding: '24px 32px 32px' }}>
                            <motion.div variants={fadeUp} custom={0} initial="hidden" animate="show">
                                <h2 className="signin-title">Welcome to Suvidha</h2>
                            </motion.div>

                            <motion.div variants={fadeUp} custom={1} initial="hidden" animate="show">
                                <p className="signin-subtitle">Enter your name to personalise your dashboard</p>
                            </motion.div>

                            {/* OAuth buttons */}
                            <motion.div variants={fadeUp} custom={2} initial="hidden" animate="show">
                                <div className="signin-oauth-wrapper">
                                    <button
                                        type="button"
                                        onClick={handleAuth0Login}
                                        className="signin-btn-oauth"
                                        disabled={loading}
                                    >
                                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                        </svg>
                                        Sign in with Auth0
                                    </button>
                                </div>
                            </motion.div>

                            <motion.div variants={fadeUp} custom={3} initial="hidden" animate="show">
                                <div className="signin-divider">
                                    <span>or continue with name</span>
                                </div>
                            </motion.div>

                            {/* Live avatar preview */}
                            <AnimatePresence>
                                {trimmed && (
                                    <motion.div
                                        className="signin-avatar-preview"
                                        initial={{ opacity: 0, y: -10, scale: 0.92 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        exit={{ opacity: 0, y: -10, scale: 0.92 }}
                                        transition={{ type: 'spring', stiffness: 320, damping: 24 }}
                                    >
                                        <div className="signin-avatar-wrap">
                                            <div
                                                className="signin-avatar"
                                                style={{ background: `linear-gradient(135deg, ${avatarFrom}, ${avatarTo})` }}
                                            >
                                                {initials || '?'}
                                            </div>
                                        </div>
                                        <div className="signin-avatar-meta">
                                            <span className="signin-avatar-name">{trimmed}</span>
                                            <span className="signin-avatar-greet">
                                                {firstName ? `Welcome, ${firstName}! ✨` : 'Ready to explore schemes?'}
                                            </span>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <motion.div variants={fadeUp} custom={4} initial="hidden" animate="show">
                                <div className="signin-field">
                                    <label htmlFor="signin-name">Your full name</label>
                                    <div className="signin-input-wrap">
                                        <input
                                            id="signin-name"
                                            type="text"
                                            value={name}
                                            onChange={(e) => { setName(e.target.value); setError('') }}
                                            placeholder="e.g. Priya Nair"
                                            autoFocus
                                            autoComplete="name"
                                        />
                                        <svg className="signin-input-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                            <circle cx="12" cy="7" r="4" />
                                        </svg>
                                    </div>
                                    {error && <div className="signin-error">{error}</div>}
                                </div>
                            </motion.div>

                            <motion.div variants={fadeUp} custom={5} initial="hidden" animate="show">
                                <button type="submit" className="signin-btn-primary" disabled={loading}>
                                    {loading ? (
                                        <>
                                            <span className="signin-spinner" />
                                            Signing you in…
                                        </>
                                    ) : (
                                        <>
                                            Continue
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M5 12h14M12 5l7 7-7 7" />
                                            </svg>
                                        </>
                                    )}
                                </button>
                            </motion.div>

                            <motion.div variants={fadeUp} custom={6} initial="hidden" animate="show">
                                <p className="signin-note">No password required · Profile stays on your device</p>
                            </motion.div>
                        </div>
                    </form>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    )
}
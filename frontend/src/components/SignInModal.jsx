import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { useAuth0 } from '@auth0/auth0-react'
import '../signin.css'

export default function SignInModal({ onClose }) {
    const { loginWithGoogle } = useAuth()
    const navigate = useNavigate()
    
    // Auth0 hook (will throw if Auth0Provider is not wrapping the app, but we only call it if env vars exist)
    const { loginWithRedirect } = useAuth0() || {}

    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // Handle Google OAuth success
    const handleGoogleSuccess = async (credentialResponse) => {
        setLoading(true)
        setError('')
        try {
            await loginWithGoogle(credentialResponse.credential)
            onClose()
            navigate('/onboarding')
        } catch (err) {
            setError('Google sign-in failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    // Handle Google OAuth error
    const handleGoogleError = () => {
        setError('Google sign-in was cancelled or failed.')
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
                {/* Modal */}
                <motion.div
                    className="signin-modal"
                    initial={{ opacity: 0, y: 24, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 16, scale: 0.97 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                    role="dialog"
                    aria-modal="true"
                    aria-label="Sign in to Suvidha"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="signin-modal-header">
                        <div className="signin-brand">
                            <div className="signin-brand-icon">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M3 21h18" /><path d="M3 10h18" /><path d="M5 6l7-3 7 3" />
                                    <path d="M4 10v11" /><path d="M20 10v11" />
                                    <path d="M8 14v3" /><path d="M12 14v3" /><path d="M16 14v3" />
                                </svg>
                            </div>
                            <span className="signin-brand-name">Suvidha</span>
                        </div>
                        <button className="signin-close" onClick={onClose} aria-label="Close">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                        </button>
                    </div>

                    <div className="signin-content">
                            <h2 className="signin-title">Welcome back</h2>
                            <p className="signin-subtitle">Sign in to access your dashboard</p>

                            {/* OAuth buttons */}
                            <div className="signin-oauth-wrapper">
                                <GoogleLogin
                                    onSuccess={handleGoogleSuccess}
                                    onError={handleGoogleError}
                                    text="signin_with"
                                    shape="rectangular"
                                    width="100%"
                                    theme="outline"
                                />
                                <div className="signin-divider"><span>OR</span></div>
                                <button
                                    type="button"
                                    onClick={handleAuth0Login}
                                    className="signin-auth0-btn"
                                >
                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                    </svg>
                                    Sign in with Auth0
                                </button>
                            </div>

                            {error && <div className="signin-error" style={{ marginTop: '16px' }}>{error}</div>}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    )
}

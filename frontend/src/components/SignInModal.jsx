import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { checkEligibility } from '../api/api'
import '../signin.css'

const INDIA_REGIONS = [
    ['AN', 'Andaman & Nicobar Islands'], ['AP', 'Andhra Pradesh'],
    ['AR', 'Arunachal Pradesh'], ['AS', 'Assam'], ['BR', 'Bihar'],
    ['CG', 'Chhattisgarh'], ['DL', 'Delhi'], ['GA', 'Goa'], ['GJ', 'Gujarat'],
    ['HR', 'Haryana'], ['HP', 'Himachal Pradesh'], ['JH', 'Jharkhand'],
    ['KA', 'Karnataka'], ['KL', 'Kerala'], ['MP', 'Madhya Pradesh'],
    ['MH', 'Maharashtra'], ['MN', 'Manipur'], ['ML', 'Meghalaya'],
    ['OD', 'Odisha'], ['PB', 'Punjab'], ['RJ', 'Rajasthan'],
    ['TN', 'Tamil Nadu'], ['TG', 'Telangana'], ['UP', 'Uttar Pradesh'],
    ['UK', 'Uttarakhand'], ['WB', 'West Bengal'],
]

export default function SignInModal({ onClose }) {
    const { signIn } = useAuth()
    const navigate = useNavigate()

    const [step, setStep] = useState(1) // 1 = name, 2 = profile
    const [name, setName] = useState('')
    const [profile, setProfile] = useState({
        age: '',
        income: '',
        gender: '',
        caste: '',
        state: '',
        education_level: '',
    })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleProfileChange = (e) =>
        setProfile((p) => ({ ...p, [e.target.name]: e.target.value }))

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!name.trim()) { setError('Please enter your name'); return }
        setError('')

        if (step === 1) { setStep(2); return }

        // Step 2 — run eligibility check with real API
        setLoading(true)
        try {
            const cleanProfile = {}
            if (profile.age) cleanProfile.age = parseInt(profile.age)
            if (profile.income) cleanProfile.income = parseFloat(profile.income)
            if (profile.gender) cleanProfile.gender = profile.gender
            if (profile.caste) cleanProfile.caste = profile.caste
            if (profile.state) cleanProfile.state = profile.state
            if (profile.education_level) cleanProfile.education_level = profile.education_level

            let eligibilityResults = null
            try {
                eligibilityResults = await checkEligibility(cleanProfile)
            } catch {
                // API might fail — sign in anyway, dashboard shows "run check" prompt
                eligibilityResults = null
            }

            signIn({ name: name.trim(), profile: cleanProfile, eligibilityResults })
            onClose()
            navigate('/dashboard')
        } finally {
            setLoading(false)
        }
    }

    const initials = name
        .trim()
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0].toUpperCase())
        .join('')

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

                    {/* Step indicator */}
                    <div className="signin-steps">
                        <div className={`signin-step-dot ${step >= 1 ? 'active' : ''}`} />
                        <div className="signin-step-line" />
                        <div className={`signin-step-dot ${step >= 2 ? 'active' : ''}`} />
                    </div>

                    <form onSubmit={handleSubmit} noValidate>
                        <AnimatePresence mode="wait">
                            {step === 1 ? (
                                <motion.div
                                    key="step1"
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ duration: 0.22 }}
                                >
                                    <div className="signin-step-label">Step 1 of 2</div>
                                    <h2 className="signin-title">Welcome to Suvidha</h2>
                                    <p className="signin-subtitle">Enter your name to personalise your dashboard</p>

                                    {/* Avatar preview */}
                                    {name.trim() && (
                                        <motion.div
                                            className="signin-avatar-preview"
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <div className="signin-avatar">{initials || '?'}</div>
                                            <span className="signin-avatar-name">{name.trim()}</span>
                                        </motion.div>
                                    )}

                                    <div className="signin-field">
                                        <label htmlFor="signin-name">Your full name</label>
                                        <input
                                            id="signin-name"
                                            type="text"
                                            value={name}
                                            onChange={(e) => { setName(e.target.value); setError('') }}
                                            placeholder="e.g. Priya Nair"
                                            autoFocus
                                            autoComplete="name"
                                        />
                                        {error && <div className="signin-error">{error}</div>}
                                    </div>

                                    <button type="submit" className="signin-btn-primary">
                                        Continue
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M5 12h14M12 5l7 7-7 7" />
                                        </svg>
                                    </button>

                                    <p className="signin-note">No password required · Profile stays on your device</p>
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="step2"
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    transition={{ duration: 0.22 }}
                                >
                                    <div className="signin-step-label">Step 2 of 2</div>
                                    <h2 className="signin-title">Your Profile</h2>
                                    <p className="signin-subtitle">
                                        Fill in any fields that apply — used only to match you with real schemes
                                    </p>

                                    <div className="signin-grid-2">
                                        <div className="signin-field">
                                            <label htmlFor="si-age">Age</label>
                                            <input id="si-age" type="number" name="age" value={profile.age}
                                                onChange={handleProfileChange} placeholder="e.g. 20" min="0" max="100" />
                                        </div>
                                        <div className="signin-field">
                                            <label htmlFor="si-income">Annual Income (₹)</label>
                                            <input id="si-income" type="number" name="income" value={profile.income}
                                                onChange={handleProfileChange} placeholder="e.g. 200000" min="0" />
                                        </div>
                                    </div>

                                    <div className="signin-grid-2">
                                        <div className="signin-field">
                                            <label htmlFor="si-gender">Gender</label>
                                            <select id="si-gender" name="gender" value={profile.gender} onChange={handleProfileChange}>
                                                <option value="">Any</option>
                                                <option value="male">Male</option>
                                                <option value="female">Female</option>
                                                <option value="others">Others</option>
                                            </select>
                                        </div>
                                        <div className="signin-field">
                                            <label htmlFor="si-caste">Category</label>
                                            <select id="si-caste" name="caste" value={profile.caste} onChange={handleProfileChange}>
                                                <option value="">Any</option>
                                                <option value="SC">SC</option>
                                                <option value="ST">ST</option>
                                                <option value="OBC">OBC</option>
                                                <option value="general">General</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="signin-grid-2">
                                        <div className="signin-field">
                                            <label htmlFor="si-state">State</label>
                                            <select id="si-state" name="state" value={profile.state} onChange={handleProfileChange}>
                                                <option value="">Any / All India</option>
                                                {INDIA_REGIONS.map(([code, label]) => (
                                                    <option key={code} value={code}>{label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="signin-field">
                                            <label htmlFor="si-edu">Education Level</label>
                                            <select id="si-edu" name="education_level" value={profile.education_level} onChange={handleProfileChange}>
                                                <option value="">Any</option>
                                                <option value="7th_pass">7th Pass</option>
                                                <option value="8th_pass">8th Pass</option>
                                                <option value="10th_pass">10th Pass</option>
                                                <option value="12th_pass">12th Pass</option>
                                                <option value="graduate">Graduate</option>
                                                <option value="post_graduate">Post Graduate</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="signin-actions">
                                        <button
                                            type="button"
                                            className="signin-btn-ghost"
                                            onClick={() => setStep(1)}
                                            disabled={loading}
                                        >
                                            ← Back
                                        </button>
                                        <button type="submit" className="signin-btn-primary" disabled={loading}>
                                            {loading ? (
                                                <>
                                                    <span className="signin-spinner" />
                                                    Matching…
                                                </>
                                            ) : (
                                                <>
                                                    Go to Dashboard
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M5 12h14M12 5l7 7-7 7" />
                                                    </svg>
                                                </>
                                            )}
                                        </button>
                                    </div>

                                    <p className="signin-note">All fields optional · Profile stays on your device only</p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </form>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    )
}

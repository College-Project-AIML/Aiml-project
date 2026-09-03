import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { checkEligibility } from '../api/api'
import './onboarding.css'

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

export default function Onboarding() {
    const { user, updateProfileAndEligibility } = useAuth()
    const navigate = useNavigate()
    const [displayName, setDisplayName] = useState(user?.name?.includes('@') ? '' : user?.name || '')
    const [nameError, setNameError] = useState('')
    
    const [profile, setProfile] = useState({
        age: user?.profile?.age || '',
        income: user?.profile?.income || '',
        gender: user?.profile?.gender || '',
        caste: user?.profile?.caste || '',
        state: user?.profile?.state || '',
        education_level: user?.profile?.education_level || '',
    })
    const [loading, setLoading] = useState(false)

    const handleProfileChange = (e) =>
        setProfile((p) => ({ ...p, [e.target.name]: e.target.value }))

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!displayName.trim()) {
            setNameError('Please enter the name you would like us to use.')
            return
        }
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
            } catch (err) {
                console.error("Failed to check eligibility during onboarding", err)
            }

            updateProfileAndEligibility(cleanProfile, eligibilityResults, displayName)
            navigate('/dashboard')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="onboarding-page">
            <motion.div
                className="onboarding-container"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            >
                <div className="onboarding-header">
                    <motion.h1 
                        className="onboarding-title"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        Complete Your Profile
                    </motion.h1>
                    <motion.p 
                        className="onboarding-subtitle"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        Tell us a bit about yourself so we can match you with the best government schemes.
                    </motion.p>
                </div>

                <form onSubmit={handleSubmit} noValidate>
                    <motion.div 
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }} 
                        transition={{ delay: 0.3 }}
                    >
                        <div className="onboarding-grid">
                            <div className="onboarding-field onboarding-name-field">
                                <label htmlFor="ob-name">Your name</label>
                                <input
                                    id="ob-name"
                                    type="text"
                                    value={displayName}
                                    onChange={(e) => {
                                        setDisplayName(e.target.value)
                                        setNameError('')
                                    }}
                                    placeholder="e.g. Priya Nair"
                                    autoComplete="name"
                                    required
                                />
                                {nameError && <span className="onboarding-error">{nameError}</span>}
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-age">Age</label>
                                <input id="ob-age" type="number" name="age" value={profile.age}
                                    onChange={handleProfileChange} placeholder="e.g. 20" min="0" max="100" />
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-income">Annual Income (₹)</label>
                                <input id="ob-income" type="number" name="income" value={profile.income}
                                    onChange={handleProfileChange} placeholder="e.g. 200000" min="0" />
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-gender">Gender</label>
                                <select id="ob-gender" name="gender" value={profile.gender} onChange={handleProfileChange}>
                                    <option value="">Any</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="others">Others</option>
                                </select>
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-caste">Category</label>
                                <select id="ob-caste" name="caste" value={profile.caste} onChange={handleProfileChange}>
                                    <option value="">Any</option>
                                    <option value="SC">SC</option>
                                    <option value="ST">ST</option>
                                    <option value="OBC">OBC</option>
                                    <option value="general">General</option>
                                </select>
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-state">State</label>
                                <select id="ob-state" name="state" value={profile.state} onChange={handleProfileChange}>
                                    <option value="">Any / All India</option>
                                    {INDIA_REGIONS.map(([code, label]) => (
                                        <option key={code} value={code}>{label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="onboarding-field">
                                <label htmlFor="ob-edu">Education Level</label>
                                <select id="ob-edu" name="education_level" value={profile.education_level} onChange={handleProfileChange}>
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

                        <div className="onboarding-actions">
                            <button type="submit" className="onboarding-btn" disabled={loading}>
                                {loading ? (
                                    <>
                                        <span className="onboarding-spinner" />
                                        Finding Matches…
                                    </>
                                ) : (
                                    <>
                                        Finish & Go to Dashboard
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M5 12h14M12 5l7 7-7 7" />
                                        </svg>
                                    </>
                                )}
                            </button>
                        </div>
                    </motion.div>
                </form>
            </motion.div>
        </div>
    )
}

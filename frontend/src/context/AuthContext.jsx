import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const STORAGE_KEY = 'suvidha-user'
const TOKEN_KEY = 'suvidha-token'

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            return stored ? JSON.parse(stored) : null
        } catch {
            return null
        }
    })

    const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))

    const signIn = (userData) => {
        // userData: { name, profile, eligibilityResults }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
        setUser(userData)
    }

    const signOut = () => {
        localStorage.removeItem(STORAGE_KEY)
        localStorage.removeItem(TOKEN_KEY)
        setUser(null)
        setToken(null)
    }

    const updateEligibility = (eligibilityResults) => {
        const updated = { ...user, eligibilityResults }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        setUser(updated)
    }

    const updateProfileAndEligibility = (profile, eligibilityResults, displayName = user?.name) => {
        const updated = { ...user, name: displayName?.trim() || user?.name, profile, eligibilityResults }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        setUser(updated)
    }

    const updateDisplayName = (name) => {
        const updated = { ...user, name: name.trim() }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        setUser(updated)
    }

    const loginWithGoogle = useCallback(async (googleCredential) => {
        try {
            const res = await fetch('/api/v1/auth/google/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential: googleCredential }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || 'OAuth verification failed')
            }

            const data = await res.json()
            // data: { access_token, user_id, name, email, avatar_url }
            localStorage.setItem(TOKEN_KEY, data.access_token)

            const userData = {
                name: data.name,
                email: data.email,
                avatar_url: data.avatar_url || null,
                user_id: data.user_id,
                oauth: true,
                profile: null,
                eligibilityResults: null,
            }
            localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
            setUser(userData)
            setToken(data.access_token)
            return userData
        } catch (err) {
            console.error('Google OAuth error:', err)
            throw err
        }
    }, [])

    const loginWithAuth0User = useCallback((auth0UserData) => {
        const userData = {
            name: auth0UserData.name || auth0UserData.nickname || auth0UserData.email,
            email: auth0UserData.email,
            avatar_url: auth0UserData.picture || null,
            user_id: auth0UserData.sub,
            oauth: true,
            auth0: true,
            profile: null,
            eligibilityResults: null,
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
        setUser(userData)
        return userData
    }, [])

    return (
        <AuthContext.Provider value={{ user, token, signIn, signOut, updateEligibility, updateProfileAndEligibility, updateDisplayName, loginWithGoogle, loginWithAuth0User }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
    return ctx
}

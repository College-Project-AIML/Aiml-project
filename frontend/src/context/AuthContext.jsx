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

    const loginWithAuth0User = useCallback((auth0UserData) => {
        let existing = null
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            existing = stored ? JSON.parse(stored) : null
        } catch {
            existing = null
        }

        const userData = {
            name: auth0UserData.name || auth0UserData.nickname || auth0UserData.email,
            email: auth0UserData.email,
            avatar_url: auth0UserData.picture || null,
            user_id: auth0UserData.sub,
            oauth: true,
            auth0: true,
            profile: existing?.profile || null,
            eligibilityResults: existing?.eligibilityResults || null,
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
        setUser(userData)
        return userData
    }, [])

    return (
        <AuthContext.Provider value={{ user, token, signIn, signOut, updateEligibility, updateProfileAndEligibility, updateDisplayName, loginWithAuth0User }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
    return ctx
}

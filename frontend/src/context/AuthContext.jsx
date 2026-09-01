import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const STORAGE_KEY = 'suvidha-user'

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            return stored ? JSON.parse(stored) : null
        } catch {
            return null
        }
    })

    const signIn = (userData) => {
        // userData: { name, profile, eligibilityResults }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
        setUser(userData)
    }

    const signOut = () => {
        localStorage.removeItem(STORAGE_KEY)
        setUser(null)
    }

    const updateEligibility = (eligibilityResults) => {
        const updated = { ...user, eligibilityResults }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        setUser(updated)
    }

    return (
        <AuthContext.Provider value={{ user, signIn, signOut, updateEligibility }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
    return ctx
}

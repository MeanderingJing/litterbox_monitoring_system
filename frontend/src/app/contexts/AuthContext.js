// runs on the client-side (browser)
'use client' 
import { createContext, useContext, useState, useEffect } from 'react'

// A "container" for sharing authentication data
const AuthContext = createContext()

// A custom hook that any component can use to access auth data
// useAuth is a function that returns the context value (user, login, register, logout, loading)
export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  // Stores current user info (null if not logged in)
  const [user, setUser] = useState(null)
  // Prevents flickering while checking if user is already logged in
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on mount
    // This is why you stay logged in even after closing/reopening the browser!
    const token = localStorage.getItem('access_token')
    const username = localStorage.getItem('username')
    if (token && username) {
      setUser({ username, token })
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    try {
      const response = await fetch('http://192.168.40.159:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('username', data.username)
        setUser({ username: data.username, token: data.access_token })
        return { success: true }
      } else {
        return { success: false, error: data.error || data.msg }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const register = async (username, email, password) => {
    try {
      const response = await fetch('http://192.168.40.159:8000/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      })

      const data = await response.json()

      if (response.ok) {
        return { success: true }
      } else {
        return { success: false, error: data.error || data.msg }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    setUser(null)
  }

  const value = {
    user,
    login,
    register,
    logout,
    loading
  }

  // Makes available to entire app:
  // Current user info, Login/register/logout functions, Loading state
  // AuthContext.Provider: a React feature that gets automatically created when you use createContext()
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

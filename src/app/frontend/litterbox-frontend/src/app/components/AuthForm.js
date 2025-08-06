'use client'
import { useState } from 'react'
// Must import useAuth first to access the tools (login, register etc)
import { useAuth } from '../contexts/AuthContext'

export default function AuthForm() {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login, register } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let result
      if (isLogin) {
        result = await login(formData.username, formData.password)
      } else {
        result = await register(formData.username, formData.email, formData.password)
        if (result.success) {
          // Auto-login after successful registration
          result = await login(formData.username, formData.password)
        }
      }

      if (!result.success) {
        setError(result.error)
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 via-pink-500 to-blue-600 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white/20 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-white/30">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white drop-shadow-lg">
            🐱 Litterbox Monitor
          </h2>
          <p className="mt-2 text-center text-sm text-white/80">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <input
                name="username"
                type="text"
                required
                className="appearance-none relative block w-full px-4 py-3 border-0 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-2 focus:ring-white focus:z-10 sm:text-sm bg-white/90 backdrop-blur-sm shadow-lg transition-all duration-300 hover:shadow-xl focus:shadow-xl focus:bg-white"
                placeholder="Username"
                value={formData.username}
                onChange={handleChange}
              />
            </div>
            {!isLogin && (
              <div>
                <input
                  name="email"
                  type="email"
                  required
                  className="appearance-none relative block w-full px-4 py-3 border-0 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-2 focus:ring-white focus:z-10 sm:text-sm bg-white/90 backdrop-blur-sm shadow-lg transition-all duration-300 hover:shadow-xl focus:shadow-xl focus:bg-white"
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            )}
            <div>
              <input
                name="password"
                type="password"
                required
                className="appearance-none relative block w-full px-4 py-3 border-0 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-2 focus:ring-white focus:z-10 sm:text-sm bg-white/90 backdrop-blur-sm shadow-lg transition-all duration-300 hover:shadow-xl focus:shadow-xl focus:bg-white"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-200 text-sm text-center bg-red-500/20 backdrop-blur-sm rounded-lg p-3 border border-red-300/30">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white disabled:opacity-50 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
            >
              {loading ? 'Loading...' : (isLogin ? 'Sign in' : 'Register')}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              className="text-white/90 hover:text-white font-medium transition-colors duration-200 underline decoration-transparent hover:decoration-white underline-offset-4"
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? "Don't have an account? Register" : "Already have an account? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
'use client'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function CatsTab({ cats, setCats, onDataChange }) {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    breed: '',
    age: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://192.168.40.159:8000/cats', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          name: formData.name,
          breed: formData.breed || null,
          age: formData.age ? parseInt(formData.age) : null
        })
      })

      const data = await response.json()

      if (response.ok) {
        setCats(prev => [...prev, data])
        setFormData({ name: '', breed: '', age: '' })
        setShowForm(false)
        onDataChange()
      } else {
        setError(data.error || data.msg || 'Failed to add cat')
      }
    } catch (err) {
      setError('Network error')
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
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">My Cats</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          {showForm ? 'Cancel' : 'Add Cat'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Cat</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter cat's name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Breed</label>
              <input
                type="text"
                name="breed"
                value={formData.breed}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter cat's breed (optional)"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Age</label>
              <input
                type="number"
                name="age"
                min="0"
                value={formData.age}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter cat's age (optional)"
              />
            </div>
            {error && <div className="text-red-600 text-sm">{error}</div>}
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Cat'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cats.map((cat) => (
          <div key={cat.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🐱</div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">{cat.name}</h3>
                {cat.breed && <p className="text-sm text-gray-600">Breed: {cat.breed}</p>}
                {cat.age && <p className="text-sm text-gray-600">Age: {cat.age} years</p>}
              </div>
            </div>
          </div>
        ))}
      </div>

      {cats.length === 0 && !showForm && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🐱</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No cats yet</h3>
          <p className="text-gray-600">Add your first cat to get started!</p>
        </div>
      )}
    </div>
  )
}

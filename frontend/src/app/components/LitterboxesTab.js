'use client'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function LitterboxesTab({ cats, litterboxes, setLitterboxes, onDataChange }) {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    cat_id: '',
    name: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:5000/litterboxes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        setLitterboxes(prev => [...prev, data])
        setFormData({ cat_id: '', name: '' })
        setShowForm(false)
        onDataChange()
      } else {
        setError(data.error || data.msg || 'Failed to add litterbox')
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

  const getCatName = (catId) => {
    const cat = cats.find(c => c.id === catId)
    return cat ? cat.name : 'Unknown Cat'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Litterboxes</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          disabled={cats.length === 0}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {showForm ? 'Cancel' : 'Add Litterbox'}
        </button>
      </div>

      {cats.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="text-yellow-400 mr-3">⚠️</div>
            <div>
              <h3 className="text-sm font-medium text-yellow-800">No cats available</h3>
              <p className="text-sm text-yellow-700">You need to add at least one cat before creating litterboxes.</p>
            </div>
          </div>
        </div>
      )}

      {showForm && cats.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Litterbox</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Cat *</label>
              <select
                name="cat_id"
                required
                value={formData.cat_id}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select a cat</option>
                {cats.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Litterbox Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter litterbox name"
              />
            </div>
            {error && <div className="text-red-600 text-sm">{error}</div>}
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Litterbox'}
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
        {litterboxes.map((litterbox) => (
          <div key={litterbox.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">📦</div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">{litterbox.name}</h3>
                <p className="text-sm text-gray-600">Cat: {getCatName(litterbox.cat_id)}</p>
                <p className="text-xs text-gray-500">ID: {litterbox.id}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {litterboxes.length === 0 && !showForm && cats.length > 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No litterboxes yet</h3>
          <p className="text-gray-600">Add your first litterbox to get started!</p>
        </div>
      )}
    </div>
  )
}
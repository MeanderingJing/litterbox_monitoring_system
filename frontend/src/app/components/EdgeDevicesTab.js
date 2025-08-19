'use client'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function EdgeDevicesTab({ litterboxes, edgeDevices, setEdgeDevices, onDataChange }) {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    id: '',
    litterbox_id: '',
    device_name: '',
    device_type: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()

  const deviceTypes = [
    'Weight Sensor',
    'Motion Detector',
    'Camera',
    'Odor Sensor',
    'Temperature Sensor',
    'Humidity Sensor'
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:5000/edge_devices', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        setEdgeDevices(prev => [...prev, data])
        setFormData({ id: '', litterbox_id: '', device_name: '', device_type: '' })
        setShowForm(false)
        onDataChange()
      } else {
        setError(data.error || data.msg || 'Failed to add edge device')
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

  const getLitterboxName = (litterboxId) => {
    const litterbox = litterboxes.find(l => l.id === litterboxId)
    return litterbox ? litterbox.name : 'Unknown Litterbox'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Edge Devices</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          disabled={litterboxes.length === 0}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {showForm ? 'Cancel' : 'Add Edge Device'}
        </button>
      </div>

      {litterboxes.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="text-yellow-400 mr-3">⚠️</div>
            <div>
              <h3 className="text-sm font-medium text-yellow-800">No litterboxes available</h3>
              <p className="text-sm text-yellow-700">You need to add at least one litterbox before registering edge devices.</p>
            </div>
          </div>
        </div>
      )}

      {showForm && litterboxes.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Register New Edge Device</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Device ID *</label>
              <input
                type="text"
                name="id"
                required
                value={formData.id}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter unique device ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Litterbox *</label>
              <select
                name="litterbox_id"
                required
                value={formData.litterbox_id}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select a litterbox</option>
                {litterboxes.map((litterbox) => (
                  <option key={litterbox.id} value={litterbox.id}>
                    {litterbox.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Device Name *</label>
              <input
                type="text"
                name="device_name"
                required
                value={formData.device_name}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter device name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Device Type *</label>
              <select
                name="device_type"
                required
                value={formData.device_type}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select device type</option>
                {deviceTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            {error && <div className="text-red-600 text-sm">{error}</div>}
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Register Device'}
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
        {edgeDevices.map((device) => (
          <div key={device.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">📱</div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">{device.device_name}</h3>
                <p className="text-sm text-gray-600">Type: {device.device_type}</p>
                <p className="text-sm text-gray-600">Litterbox: {getLitterboxName(device.litterbox_id)}</p>
                <p className="text-xs text-gray-500">ID: {device.id}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {edgeDevices.length === 0 && !showForm && litterboxes.length > 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📱</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No edge devices yet</h3>
          <p className="text-gray-600">Register your first edge device to get started!</p>
        </div>
      )}
    </div>
  )
}
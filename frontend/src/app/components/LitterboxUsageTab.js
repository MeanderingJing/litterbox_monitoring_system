'use client'
import { useState, useEffect } from 'react'

export default function LitterboxUsageTab({ cats, user }) {
  const [selectedCat, setSelectedCat] = useState('')
  const [usageData, setUsageData] = useState([])
  // Removed stats for now - keeping it simple
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    endDate: new Date().toISOString().split('T')[0] // today
  })
  const [currentPage, setCurrentPage] = useState(0)
  const [itemsPerPage] = useState(10)

  // Set the first cat as default when cats are loaded
  useEffect(() => {
    if (cats.length > 0 && !selectedCat) {
      setSelectedCat(cats[0].id)
    }
  }, [cats, selectedCat])

  // Fetch usage data when cat or date range changes
  useEffect(() => {
    console.log('useEffect triggered:', { selectedCat, startDate: dateRange.startDate, endDate: dateRange.endDate, hasToken: !!user?.token })
    
    if (selectedCat && user?.token) {
      // Add a small delay to prevent rapid API calls when user is typing dates
      const timeoutId = setTimeout(() => {
        fetchUsageData()
      }, 300)
      
      return () => clearTimeout(timeoutId)
    } else {
      console.log('Skipping fetch - missing requirements:', { selectedCat: !!selectedCat, hasToken: !!user?.token })
      setUsageData([])
    }
  }, [selectedCat, dateRange.startDate, dateRange.endDate, user?.token])

  const fetchUsageData = async () => {
    setLoading(true)
    setError('')
    
    console.log('Fetching usage data for:', {
      selectedCat,
      dateRange,
      userToken: user?.token ? 'present' : 'missing'
    })
    
    try {
      const params = new URLSearchParams({
        start_date: `${dateRange.startDate}T00:00:00`,
        end_date: `${dateRange.endDate}T23:59:59`,
        limit: '1000' // Get plenty of data for client-side pagination
      })

      const url = `http://192.168.40.159:8000/cats/${selectedCat}/litterbox-usage?${params}`
      console.log('API URL:', url)

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Response data:', data)
        setUsageData(data.usage_data || [])
        setCurrentPage(0) // Reset to first page when new data loads
      } else {
        const errorData = await response.json()
        console.error('API Error:', errorData)
        setError(errorData.error || `Failed to fetch usage data (${response.status})`)
        setUsageData([]) // Clear data on error
      }
    } catch (error) {
      console.error('Network error fetching usage data:', error)
      setError(`Network error: ${error.message}`)
      setUsageData([]) // Clear data on error
    } finally {
      setLoading(false)
    }
  }

  // Removed stats fetching for now - keeping it simple

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const formatDuration = (minutes) => {
    if (minutes < 60) {
      return `${minutes.toFixed(1)}m`
    }
    const hours = Math.floor(minutes / 60)
    const mins = (minutes % 60).toFixed(0)
    return `${hours}h ${mins}m`
  }

  const getSelectedCatName = () => {
    const cat = cats.find(c => c.id === selectedCat)
    return cat ? cat.name : 'Unknown Cat'
  }

  // Pagination
  const totalPages = Math.ceil(usageData.length / itemsPerPage)
  const paginatedData = usageData.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  )

  const goToPage = (page) => {
    setCurrentPage(page)
  }

  if (cats.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🐱</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Cats Found</h3>
        <p className="text-gray-500">Add some cats first to view their litterbox usage data.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">📊 Litterbox Usage Analysis</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Cat Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Cat
            </label>
            <select
              value={selectedCat}
              onChange={(e) => setSelectedCat(e.target.value)}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Choose a cat...</option>
              {cats.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name} {cat.breed ? `(${cat.breed})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={dateRange.startDate}
              onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={dateRange.endDate}
              onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Usage Chart Visualization */}
      {usageData.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Timeline</h3>
          
          {/* Simple usage frequency chart */}
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Daily Usage Pattern</span>
              <span>{usageData.length} total visits</span>
            </div>
            
            {/* Group usage data by day and create simple bar chart */}
            <div className="space-y-2">
              {(() => {
                // Group usage by date
                const dailyUsage = usageData.reduce((acc, usage) => {
                  const date = new Date(usage.enter_time).toDateString()
                  acc[date] = (acc[date] || 0) + 1
                  return acc
                }, {})

                const maxVisits = Math.max(...Object.values(dailyUsage))
                
                return Object.entries(dailyUsage)
                  .sort(([a], [b]) => new Date(a) - new Date(b))
                  .map(([date, count]) => {
                    const percentage = (count / maxVisits) * 100
                    return (
                      <div key={date} className="flex items-center space-x-3">
                        <div className="w-20 text-xs text-gray-600 flex-shrink-0">
                          {new Date(date).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </div>
                        <div className="flex-1 bg-gray-200 rounded-full h-4 relative">
                          <div
                            className="bg-indigo-600 h-4 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          ></div>
                          <span className="absolute right-2 top-0 h-4 flex items-center text-xs font-medium text-white">
                            {count}
                          </span>
                        </div>
                      </div>
                    )
                  })
              })()}
            </div>

            {/* Usage time distribution */}
            <div className="mt-6">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                <span>Time of Day Distribution</span>
              </div>
              <div className="grid grid-cols-6 gap-1">
                {(() => {
                  // Group by hour
                  const hourlyUsage = Array.from({ length: 24 }, () => 0)
                  usageData.forEach(usage => {
                    const hour = new Date(usage.enter_time).getHours()
                    hourlyUsage[hour]++
                  })

                  const maxHourlyVisits = Math.max(...hourlyUsage)
                  
                  return hourlyUsage.map((count, hour) => {
                    const intensity = maxHourlyVisits > 0 ? (count / maxHourlyVisits) : 0
                    return (
                      <div key={hour} className="text-center">
                        <div
                          className="w-full h-12 bg-gray-200 rounded mb-1 flex items-end justify-center text-xs font-medium transition-all duration-300 hover:bg-indigo-100"
                          style={{
                            backgroundColor: intensity > 0 
                              ? `rgba(79, 70, 229, ${0.2 + intensity * 0.8})` 
                              : '#e5e7eb'
                          }}
                          title={`${hour}:00 - ${count} visits`}
                        >
                          {count > 0 && (
                            <span className="text-white text-xs font-bold mb-1">
                              {count}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {hour < 10 ? `0${hour}` : hour}
                        </div>
                      </div>
                    )
                  })
                })()}
              </div>
            </div>

            {/* Quick stats summary */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">
                  {usageData.length}
                </div>
                <div className="text-xs text-gray-500">Total Visits</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {(usageData.reduce((sum, usage) => sum + usage.duration_minutes, 0) / usageData.length).toFixed(1)}m
                </div>
                <div className="text-xs text-gray-500">Avg Duration</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {(usageData.reduce((sum, usage) => sum + usage.cat_weight, 0) / usageData.length).toFixed(1)}g
                </div>
                <div className="text-xs text-gray-500">Avg Weight Δ</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {(() => {
                    const days = Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24)) + 1
                    return (usageData.length / days).toFixed(1)
                  })()}
                </div>
                <div className="text-xs text-gray-500">Visits/Day</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards - Removed for simplicity */}

      {/* Usage Data Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Usage Data for {getSelectedCatName()}
          </h3>
          {usageData.length > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              Showing {paginatedData.length} of {usageData.length} visits
            </p>
          )}
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="text-4xl mb-4">🔄</div>
            <div className="text-gray-600">Loading usage data...</div>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <div className="text-4xl mb-4">❌</div>
            <div className="text-red-600 mb-2">{error}</div>
            <button
              onClick={() => fetchUsageData()}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Retry
            </button>
          </div>
        ) : usageData.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-4xl mb-4">📭</div>
            <div className="text-gray-600">No usage data found for the selected period</div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cat Weight
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Device
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Litterbox
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {paginatedData.map((usage) => (
                    <tr key={usage.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>{formatDateTime(usage.enter_time)}</div>
                        <div className="text-xs text-gray-500">
                          to {formatDateTime(usage.exit_time)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDuration(usage.duration_minutes)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className='text-green-600'>
                          {usage.cat_weight.toFixed(1)} lb
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {usage.device_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {usage.litterbox_name}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage === 0}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage === totalPages - 1}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing page <span className="font-medium">{currentPage + 1}</span> of{' '}
                      <span className="font-medium">{totalPages}</span>
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 0}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      {Array.from({ length: totalPages }, (_, i) => (
                        <button
                          key={i}
                          onClick={() => goToPage(i)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            i === currentPage
                              ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {i + 1}
                        </button>
                      ))}
                      <button
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages - 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
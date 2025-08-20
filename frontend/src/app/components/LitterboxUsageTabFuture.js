'use client'
import { useState, useEffect } from 'react'

export default function LitterboxUsageTab({ cats, user }) {
  const [selectedCat, setSelectedCat] = useState('')
  const [usageData, setUsageData] = useState([])
  const [stats, setStats] = useState(null)
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
    if (selectedCat && user?.token) {
      fetchUsageData()
    //   fetchUsageStats()
    }
  }, [selectedCat, dateRange.startDate, dateRange.endDate, user?.token])

  const fetchUsageData = async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        start_date: `${dateRange.startDate}T00:00:00`,
        end_date: `${dateRange.endDate}T23:59:59`,
        limit: '1000' // Get plenty of data for client-side pagination
      })

      const response = await fetch(
        `http://192.168.40.159:8000/cats/${selectedCat}/litterbox-usage?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setUsageData(data.usage_data || [])
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch usage data')
      }
    } catch (error) {
      console.error('Error fetching usage data:', error)
      setError('Network error occurred')
    } finally {
      setLoading(false)
    }
  }

//   const fetchUsageStats = async () => {
//     try {
//       const daysDiff = Math.ceil((new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24))
//       const response = await fetch(
//         `http://192.168.40.159:8000/cats/${selectedCat}/litterbox-usage/stats?days=${daysDiff}`,
//         {
//           headers: {
//             'Authorization': `Bearer ${user.token}`
//           }
//         }
//       )

//       if (response.ok) {
//         const data = await response.json()
//         setStats(data.stats)
//       }
//     } catch (error) {
//       console.error('Error fetching stats:', error)
//     }
//   }

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

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl">📈</div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Visits
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_visits}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl">⏱️</div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Duration
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {formatDuration(stats.average_duration_minutes)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl">⚖️</div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Weight Change
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.average_weight_change_grams.toFixed(1)}g
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-2xl">📊</div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Visits/Day
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.visits_per_day.toFixed(1)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

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
            <div className="text-red-600">{error}</div>
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
                      Weight Change
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
                        <span className={usage.weight_difference >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {usage.weight_difference >= 0 ? '+' : ''}{usage.weight_difference.toFixed(1)}g
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
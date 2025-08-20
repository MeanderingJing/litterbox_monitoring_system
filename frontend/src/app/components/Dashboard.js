'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import CatsTab from './CatsTab'
import LitterboxesTab from './LitterboxesTab'
import EdgeDevicesTab from './EdgeDevicesTab'
import LitterboxUsageTab from './LitterboxUsageTab'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('cats')
  const [cats, setCats] = useState([])
  const [litterboxes, setLitterboxes] = useState([])
  const [edgeDevices, setEdgeDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const { user, logout } = useAuth()

  const tabs = [
    { id: 'cats', name: 'Cats', icon: '🐱' },
    { id: 'litterboxes', name: 'Litterboxes', icon: '📦' },
    { id: 'devices', name: 'Edge Devices', icon: '📱' },
    { id: 'usage', name: 'Litterbox Usage', icon: '📊' } // Future feature
  ]

  // Fetch all data when component mounts
  useEffect(() => {
    if (user?.token) {
      fetchAllData()
    }
  }, [user])

  const fetchAllData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        fetchCats(),
        fetchLitterboxes(),
        fetchEdgeDevices()
      ])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchCats = async () => {
    try {
      const response = await fetch('http://192.168.40.159:8000/cats', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setCats(data)
      }
    } catch (error) {
      console.error('Error fetching cats:', error)
    }
  }

  const fetchLitterboxes = async () => {
    try {
      const response = await fetch('http://192.168.40.159:8000/litterboxes', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setLitterboxes(data)
      }
    } catch (error) {
      console.error('Error fetching litterboxes:', error)
    }
  }

  const fetchEdgeDevices = async () => {
    try {
      const response = await fetch('http://192.168.40.159:8000/edge_devices', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setEdgeDevices(data)
      }
    } catch (error) {
      console.error('Error fetching edge devices:', error)
    }
  }

  const refreshData = () => {
    fetchAllData()
  }


  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-4xl mb-4">🐱</div>
          <div className="text-lg text-gray-600">Loading your data...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                🐱 Litterbox Monitor
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user.username}!</span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="mt-6">
            {activeTab === 'cats' && (
              <CatsTab 
                cats={cats} 
                setCats={setCats} 
                onDataChange={refreshData}
              />
            )}
            {activeTab === 'litterboxes' && (
              <LitterboxesTab 
                cats={cats}
                litterboxes={litterboxes}
                setLitterboxes={setLitterboxes}
                onDataChange={refreshData}
              />
            )}
            {activeTab === 'devices' && (
              <EdgeDevicesTab 
                litterboxes={litterboxes}
                edgeDevices={edgeDevices}
                setEdgeDevices={setEdgeDevices}
                onDataChange={refreshData}
              />
            )}
            {activeTab === 'usage' && (
              <LitterboxUsageTab 
                cats={cats}
                user={user}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// 'use client'
// import { useState } from 'react'
// import { useAuth } from '../contexts/AuthContext'
// import CatsTab from './CatsTab'
// import LitterboxesTab from './LitterboxesTab'
// import EdgeDevicesTab from './EdgeDevicesTab'

// export default function Dashboard() {
//   const [activeTab, setActiveTab] = useState('cats')
//   const [cats, setCats] = useState([])
//   const [litterboxes, setLitterboxes] = useState([])
//   const [edgeDevices, setEdgeDevices] = useState([])
//   const { user, logout } = useAuth()

//   const tabs = [
//     { id: 'cats', name: 'Cats', icon: '🐱' },
//     { id: 'litterboxes', name: 'Litterboxes', icon: '📦' },
//     { id: 'devices', name: 'Edge Devices', icon: '📱' }
//   ]

//   const refreshData = () => {
//     // This would fetch updated data from your backend
//     // For now, we'll trigger re-renders of child components
//   }

//   return (
//     <div className="min-h-screen bg-gray-50">
//       <nav className="bg-white shadow">
//         <div className="max-w-7xl mx-auto px-4">
//           <div className="flex justify-between h-16">
//             <div className="flex items-center">
//               <h1 className="text-xl font-semibold text-gray-900">
//                 🐱 Litterbox Monitor
//               </h1>
//             </div>
//             <div className="flex items-center space-x-4">
//               <span className="text-gray-700">Welcome, {user.username}!</span>
//               <button
//                 onClick={logout}
//                 className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium"
//               >
//                 Logout
//               </button>
//             </div>
//           </div>
//         </div>
//       </nav>

//       <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
//         <div className="px-4 py-6 sm:px-0">
//           <div className="border-b border-gray-200">
//             <nav className="-mb-px flex space-x-8">
//               {tabs.map((tab) => (
//                 <button
//                   key={tab.id}
//                   onClick={() => setActiveTab(tab.id)}
//                   className={`${
//                     activeTab === tab.id
//                       ? 'border-indigo-500 text-indigo-600'
//                       : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
//                   } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
//                 >
//                   <span>{tab.icon}</span>
//                   <span>{tab.name}</span>
//                 </button>
//               ))}
//             </nav>
//           </div>

//           <div className="mt-6">
//             {activeTab === 'cats' && (
//               <CatsTab 
//                 cats={cats} 
//                 setCats={setCats} 
//                 onDataChange={refreshData}
//               />
//             )}
//             {activeTab === 'litterboxes' && (
//               <LitterboxesTab 
//                 cats={cats}
//                 litterboxes={litterboxes}
//                 setLitterboxes={setLitterboxes}
//                 onDataChange={refreshData}
//               />
//             )}
//             {activeTab === 'devices' && (
//               <EdgeDevicesTab 
//                 litterboxes={litterboxes}
//                 edgeDevices={edgeDevices}
//                 setEdgeDevices={setEdgeDevices}
//                 onDataChange={refreshData}
//               />
//             )}
//           </div>
//         </div>
//       </div>
//     </div>
//   )
// }

import { useEffect, useState } from 'react'

function AdminDashboard() {
    // Stores the services retrieved from the backend
    const [services, setServices] = useState([])
    const [queueCounts, setQueueCounts] = useState({})

    // Loads services when dashboard opens
    useEffect(() => {
      async function loadServices() {
        try {
          const response = await fetch('/api/services/')

          if (!response.ok) {
            throw new Error('Could not load services.')
          }

          const data = await response.json()
          setServices(data)

          const counts = await Promise.all(
            data.map(async (service) => {
              const countResponse = await fetch(
                `/api/queues/${service.id}/count`
              )

              if (!countResponse.ok) {
                throw new Error('Could not load queue counts.')
              }

              const countData = await countResponse.json()
              return [service.id, countData.count]
             })
          )

          setQueueCounts(Object.fromEntries(counts))

        } catch (error) {
          console.error('Error loading services:', error)
        }
      }

      loadServices()
    }, [])

    return (
    <div>
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      <p className="mt-2">Location: Downtown Houston</p>

      <a
        href="/admin-queue"
        className="mt-4 inline-block border border-slate-300 px-3 py-2"
      >
        Manage Queues
      </a>

      <div className="mt-6">
        <h2 className="text-xl font-semibold">Services</h2>

        {/* Displays the services returned by the backend */}
        <div className="mt-4">         
          {services.map((service) => (
            <div
              className="mb-3 border border-slate-200 bg-white p-4"
              key={service.name}
            >
              <h3 className="font-semibold">{service.name}</h3>

              <p className="mt-1">
                People waiting: {queueCounts[service.id] ?? 'Loading...'}
              </p>

              <p className="mt-1">
                Expected duration: {service.expected_duration} minutes
              </p>
            </div>
          ))}

        </div>

      </div>
    </div>
  )
}

export default AdminDashboard
import { useEffect, useState } from 'react'

function AdminDashboard() {
    // Stores the services retrieved from the backend
    const [services, setServices] = useState([])

    // Loades services when dashboard opens
    useEffect(() => {
      async function loadServices() {
        try {
          const response = await fetch('/api/services/')

          if (!response.ok) {
            throw new Error('Could not load services.')
          }

          const data = await response.json()
          setServices(data)
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

      <div className="mt-6">
        <h2 className="text-xl font-semibold">Services</h2>

        {/* Displays the services returned by the backend */}
        <div className="mt-4">
            {services.map((service) => (
                <div className="mb-3 border border-slate-200 bg-white p-4" key={service.name}>
                    <h3 className="font-semibold">{service.name}</h3>
                    <p className="mt-1">
                      Expected duration: {service.expected_duration} minutes
                    </p>
                    <p className="mt-1">
                        Status: {service.isOpen ? 'Open' : 'Closed'}
                    </p>

                    <button
                        onClick={() => {
                            setServices(
                                services.map((item) =>
                                    item.name === service.name
                                        ? { ...item, isOpen: !item.isOpen }
                                        : item
                                )
                            )
                        }}
                        className="mt-3 border border-slate-300 px-3 py-1"
                    >
                            {service.isOpen ? 'Close Queue' : 'Open Queue'}
                    </button>
                  </div>
            ))}
          </div>

      </div>
    </div>
  )
}

export default AdminDashboard
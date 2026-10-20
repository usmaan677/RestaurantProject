import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { notifications } from '../mockData'

function Dashboard() {
  const user = JSON.parse(localStorage.getItem('user'))

  const [services, setServices] = useState([])
  const [counts, setCounts] = useState({})
  const [myQueues, setMyQueues] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    async function loadDashboard() {
      const servicesResponse = await fetch('/api/services/')
      const servicesData = servicesResponse.ok ? await servicesResponse.json() : []
      setServices(servicesData)

      const countEntries = await Promise.all(
        servicesData.map(async (service) => {
          const response = await fetch(`/api/queues/${service.id}/count`)
          const data = response.ok ? await response.json() : { count: 0 }
          return [service.id, data.count]
        })
      )
      setCounts(Object.fromEntries(countEntries))

      const myQueuesResponse = await fetch(`/api/queues/mine?email=${encodeURIComponent(user.email)}`)
      setMyQueues(myQueuesResponse.ok ? await myQueuesResponse.json() : [])

      setLoading(false)
    }

    loadDashboard()
  }, [])

  function serviceName(serviceId) {
    const service = services.find((s) => s.id === serviceId)
    return service ? service.name : 'Unknown service'
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
        <p className="mt-4 text-slate-600">
          Please <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to see your dashboard.
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
        <p className="mt-4 text-slate-600">Loading...</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
      <p className="mt-2 text-slate-600">Here's what's happening with your orders.</p>

      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-800">Current Queue</h2>
        {myQueues.length === 0 && <p className="mt-1 text-slate-600">You are not in any queues right now.</p>}
        {myQueues.map((queue) => (
          <p key={queue.service_id} className="mt-1 text-slate-600">
            You are in line for <span className="font-medium">{serviceName(queue.service_id)}</span> position #
            {queue.position}, about {queue.estimated_wait} minutes.
          </p>
        ))}
        <Link to="/queue-status" className="mt-2 inline-block text-blue-600 hover:underline">
          View queue status
        </Link>
      </div>

      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-800">Active Services</h2>
        <ul className="mt-2 flex flex-col gap-2">
          {services.map((service) => (
            <li key={service.id} className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-0">
              <div>
                <p className="font-medium text-slate-800">{service.name}</p>
                <p className="text-sm text-slate-600">
                  {counts[service.id] ?? 0} in line · {service.expected_duration} min per person
                </p>
              </div>
              <Link to="/join-queue" className="text-sm text-blue-600 hover:underline">
                Join
              </Link>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-800">Notifications</h2>
        <ul className="mt-2 flex flex-col gap-2">
          {notifications.map((note) => (
            <li key={note.id} className="border-b border-slate-100 pb-2 last:border-0">
              <p className="text-slate-800">{note.message}</p>
              <p className="text-sm text-slate-500">{note.time}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default Dashboard

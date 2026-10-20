import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function QueueStatus() {
  const user = JSON.parse(localStorage.getItem('user'))

  const [services, setServices] = useState([])
  const [myQueues, setMyQueues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    loadStatus()
  }, [])

  async function loadStatus() {
    setLoading(true)
    setError('')

    const servicesResponse = await fetch('/api/services/')
    setServices(servicesResponse.ok ? await servicesResponse.json() : [])

    const myQueuesResponse = await fetch(`/api/queues/mine?email=${encodeURIComponent(user.email)}`)
    setMyQueues(myQueuesResponse.ok ? await myQueuesResponse.json() : [])

    setLoading(false)
  }

  async function handleLeave(serviceId) {
    try {
      setError('')

      const response = await fetch('/api/queues/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email, service_id: serviceId }),
      })

      if (!response.ok) {
        const result = await response.json()
        throw new Error(result.detail || 'Could not leave the queue.')
      }

      loadStatus()
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    }
  }

  function serviceName(serviceId) {
    const service = services.find((s) => s.id === serviceId)
    return service ? service.name : 'Unknown service'
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>
        <p className="mt-4 text-slate-600">
          Please <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to see your queue status.
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>
        <p className="mt-4 text-slate-600">Loading...</p>
      </div>
    )
  }

  if (myQueues.length === 0) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>
        <p className="mt-4 text-slate-600">You are not currently in a queue.</p>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <Link to="/join-queue" className="mt-4 inline-block text-blue-600 hover:underline">
          Join a queue
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {myQueues.map((queue) => (
        <div key={queue.service_id} className="mt-6 rounded border border-slate-200 bg-white p-4">
          <p className="text-lg font-medium text-slate-800">{serviceName(queue.service_id)}</p>
          <p className="mt-2 text-slate-600">Position in queue: #{queue.position}</p>
          <p className="text-slate-600">Estimated wait: {queue.estimated_wait} minutes</p>

          <button
            onClick={() => handleLeave(queue.service_id)}
            className="mt-4 rounded border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100"
          >
            Leave Queue
          </button>
        </div>
      ))}
    </div>
  )
}

export default QueueStatus

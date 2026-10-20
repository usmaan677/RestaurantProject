import { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'

// Same made-up id as JoinQueue.jsx - there's no login system yet,
// so this is how the backend tells "you" apart from other users.
function getUserId() {
  let id = localStorage.getItem('queuesmart_user_id')

  if (!id) {
    id = String(Math.floor(Math.random() * 1000000) + 1)
    localStorage.setItem('queuesmart_user_id', id)
  }

  return Number(id)
}

function QueueStatus() {
  // JoinQueue sends us the chosen service id.
  const location = useLocation()
  const serviceId = location.state?.serviceId

  const [service, setService] = useState(null)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  // Becomes true when the user clicks "Leave Queue".
  // It only lives on this page, so it resets when the page reloads.
  const [left, setLeft] = useState(false)

  useEffect(() => {
    async function loadStatus() {
      if (!serviceId) {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError('')

        const userId = getUserId()

        const [serviceResponse, statusResponse] = await Promise.all([
          fetch(`/api/services/${serviceId}`),
          fetch(`/api/queues/${serviceId}/position/${userId}`),
        ])

        setService(serviceResponse.ok ? await serviceResponse.json() : null)
        setStatus(statusResponse.ok ? await statusResponse.json() : null)
      } catch (err) {
        setError(err.message || 'Could not connect to the backend.')
      } finally {
        setLoading(false)
      }
    }

    loadStatus()
  }, [serviceId])

  async function handleLeave() {
    if (!serviceId) {
      return
    }

    try {
      setError('')

      const response = await fetch('/api/queues/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: getUserId(), service_id: serviceId }),
      })

      if (!response.ok) {
        const result = await response.json()
        throw new Error(result.detail || 'Could not leave the queue.')
      }

      setLeft(true)
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    }
  }

  if (loading) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>
        <p className="mt-4 text-slate-600">Loading...</p>
      </div>
    )
  }

  // Nothing to show if there's no service chosen, the user isn't in the queue, or they left
  if (!serviceId || !status || left) {
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

      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <p className="text-lg font-medium text-slate-800">{service?.name}</p>
        <p className="mt-2 text-slate-600">Position in queue: #{status.position}</p>
        <p className="text-slate-600">Estimated wait: {status.estimated_wait} minutes</p>
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <button
        onClick={handleLeave}
        className="mt-4 rounded border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100"
      >
        Leave Queue
      </button>
    </div>
  )
}

export default QueueStatus

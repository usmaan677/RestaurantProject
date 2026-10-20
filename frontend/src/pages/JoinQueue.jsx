import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// There's no login system yet, so we make up an id for this browser
// and remember it, so the backend can tell "you" apart from other users.
function getUserId() {
  let id = localStorage.getItem('queuesmart_user_id')

  if (!id) {
    id = String(Math.floor(Math.random() * 1000000) + 1)
    localStorage.setItem('queuesmart_user_id', id)
  }

  return Number(id)
}

function JoinQueue() {
  // Services loaded from the backend
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  // The id of the service picked in the dropdown ('' means nothing picked yet)
  const [selectedId, setSelectedId] = useState('')
  const [joining, setJoining] = useState(false)
  // Error message shown under the dropdown
  const [error, setError] = useState('')
  const navigate = useNavigate()

  // Load the real list of services when the page opens
  useEffect(() => {
    async function loadServices() {
      try {
        const response = await fetch('/api/services/')

        if (!response.ok) {
          throw new Error('Could not load services.')
        }

        setServices(await response.json())
      } catch (err) {
        setError(err.message || 'Could not connect to the backend.')
      } finally {
        setLoading(false)
      }
    }

    loadServices()
  }, [])

  // Look up the full service object for the picked id (dropdown values are strings, so convert)
  const selectedService = services.find((s) => s.id === Number(selectedId))

  async function handleJoin(e) {
    // Stop the browser from reloading the page on submit
    e.preventDefault()

    if (!selectedId) {
      setError('Please select a service before joining a queue.')
      return
    }

    setError('')
    setJoining(true)

    try {
      const response = await fetch('/api/queues/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: getUserId(),
          service_id: Number(selectedId),
          priority: 1,
        }),
      })

      const result = await response.json()

      // A 400 here just means we already joined this queue before - that's fine,
      // go straight to the status page instead of showing an error.
      if (!response.ok && response.status !== 400) {
        throw new Error(result.detail || 'Could not join the queue.')
      }

      // Go to the status page and pass along which service was chosen
      navigate('/queue-status', { state: { serviceId: Number(selectedId) } })
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    } finally {
      setJoining(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-3xl font-bold text-slate-800">Join a Queue</h1>
      <p className="mt-2 text-slate-600">Choose a service to join the queue for.</p>

      <form onSubmit={handleJoin} className="mt-6 flex flex-col gap-4">
        <div>
          <label htmlFor="service" className="block text-sm font-medium text-slate-700">
            Service
          </label>
          <select
            id="service"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          >
            <option value="">{loading ? 'Loading services...' : 'Select a service'}</option>
            {services.map((service) => (
              <option key={service.id} value={service.id}>
                {service.name}
              </option>
            ))}
          </select>
          {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>

        {/* Details only appear once a service is picked */}
        {selectedService && (
          <div className="rounded border border-slate-200 bg-white p-3">
            <p className="text-slate-700">{selectedService.description}</p>
            <p className="mt-1 text-sm text-slate-600">
              Expected duration per person: {selectedService.expected_duration} minutes
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={joining}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {joining ? 'Joining...' : 'Join Queue'}
        </button>
      </form>
    </div>
  )
}

export default JoinQueue

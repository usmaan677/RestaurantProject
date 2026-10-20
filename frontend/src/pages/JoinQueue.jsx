import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

function JoinQueue() {
  const user = JSON.parse(localStorage.getItem('user'))

  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

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

  const selectedService = services.find((s) => s.id === Number(selectedId))

  async function handleJoin(e) {
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
          email: user.email,
          service_id: Number(selectedId),
          priority: 1,
        }),
      })

      const result = await response.json()

      if (!response.ok && response.status !== 400) {
        throw new Error(result.detail || 'Could not join the queue.')
      }

      navigate('/queue-status')
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    } finally {
      setJoining(false)
    }
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Join a Queue</h1>
        <p className="mt-4 text-slate-600">Please log in to join a queue.</p>
      </div>
    )
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

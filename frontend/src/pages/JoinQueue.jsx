import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { services } from '../mockData'

function JoinQueue() {
  const [selectedId, setSelectedId] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const selectedService = services.find((s) => s.id === Number(selectedId))

  function handleJoin(e) {
    e.preventDefault()

    if (!selectedId) {
      setError('Please select a service before joining a queue.')
      return
    }

    setError('')
    navigate('/queue-status', { state: { serviceId: Number(selectedId) } })
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
            <option value="">Select a service</option>
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
              Estimated wait time: {selectedService.waitTime} minutes
            </p>
          </div>
        )}

        <button
          type="submit"
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          Join Queue
        </button>
      </form>
    </div>
  )
}

export default JoinQueue

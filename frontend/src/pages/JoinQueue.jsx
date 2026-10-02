import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
// The list of services comes from the mockData file
import { services } from '../mockData'

function JoinQueue() {
  // The id of the service picked in the dropdown ('' means nothing picked yet)
  const [selectedId, setSelectedId] = useState('')
  // Error message shown under the dropdown
  const [error, setError] = useState('')
  const navigate = useNavigate()

  // Look up the full service object for the picked id (dropdown values are strings, so convert)
  const selectedService = services.find((s) => s.id === Number(selectedId))

  function handleJoin(e) {
    // Stop the browser from reloading the page on submit
    e.preventDefault()

    if (!selectedId) {
      setError('Please select a service before joining a queue.')
      return
    }

    setError('')
    // Go to the status page and pass along which service was chosen
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

        {/* Details only appear once a service is picked */}
        {selectedService && (
          <div className="rounded border border-slate-200 bg-white p-3">
            <p className="text-slate-700">{selectedService.description}</p>
            <p className="mt-1 text-sm text-slate-600">
              {selectedService.queue.length} in line · Estimated wait time: {selectedService.waitTime} minutes
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

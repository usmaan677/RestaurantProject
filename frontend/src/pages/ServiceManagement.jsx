import { useEffect, useState } from 'react'

function ServiceManagement() {
  const [showForm, setShowForm] = useState(false)
  const [serviceName, setServiceName] = useState('')
  const [description, setDescription] = useState('')
  const [duration, setDuration] = useState('')
  const [priority, setPriority] = useState('Medium')
  const [editingService, setEditingService] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // Stores the services loaded from the backend
  const [services, setServices] = useState([])

  // Gets the current services from backend
  async function loadServices() {
    try {
      setLoading(true)
      setError('')

      const response = await fetch('/api/services/')

      if(!response.ok) {
        throw new Error('Could not load services.')
      }

      const data = await response.json()
      setServices(data)
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    } finally {
      setLoading(false)
    }
  }
  // Loads services when the page first opens
  useEffect(() => {
    loadServices()
  }, [])


  // Creates a new service or updates an existing one
  async function saveService() {
    setError('')

    if (!serviceName || !description || !duration) {
      alert('Please fill in all required fields.')
      return
    }

    if (!Number.isInteger(Number(duration)) || Number(duration) <= 0) {
      setError('Duration must be a positive whole number.')
      return
    }

    const priorityNumber = {
      Low: 1,
      Medium: 3,
      High: 5,
    }[priority]

    const serviceData = {
      name: serviceName,
      description: description,
      expected_duration: Number(duration),
      priority: priorityNumber,
    }

    try {
      let response

      if (editingService) {
        response = await fetch(`/api/services/${editingService.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json'},
          body: JSON.stringify(serviceData),
      })
      } else {
        response = await fetch('/api/services/', {
          method: "POST",
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(serviceData)
        })
      }

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          Array.isArray(result.detail)
            ? result.detail.map((item) => item.msg).join(', ')
            : result.detail || 'Could not save service.'
        )
      }

      await loadServices()

      setShowForm(false)
      setEditingService('')
      setServiceName('')
      setDescription('')
      setDuration('')
      setPriority('Medium')
    } catch (err) {
      setError(err.message || 'Could not connect to the backend.')
    }
  }


  // Fills the form with the selected service's information
  function editService(service) {
    setEditingService(service)
    setServiceName(service.name)
    setDescription(service.description)
    setDuration(String(service.expected_duration))
    setPriority(
      service.priority <= 2
        ? 'Low'
        : service.priority >= 4
          ?'High'
          :'Medium'
    )
    setError('')
    setShowForm(true)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Service Management</h1>
      <p className="mt-2">Manage services for Downtown Houston.</p>

      <h2 className="mt-6 text-xl font-semibold">Current Services</h2>
      {loading && <p className="mt-3">Loading services...</p>}

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <button
        onClick={() => {
          setEditingService('')
          setShowForm(true)
        }}
        className="mt-3 border border-slate-300 px-3 py-1"
      >
        Create Service
      </button>

      {showForm && (
        <div className="mt-4 border border-slate-200 bg-white p-4">
          <h2 className="text-xl font-semibold">Service</h2>

          <label className="mt-4 block font-medium">Service Name <small className="text-red-500">(required)</small></label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            maxLength={100}
            className="mt-1 w-full border border-slate-300 p-2"
            placeholder="Enter service name"
          />

          <label className="mt-4 block font-medium">Description <small className="text-red-500">(required)</small></label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full border border-slate-300 p-2"
            placeholder="Enter service description"
          />

          <label className="mt-4 block font-medium">
            Expected Duration (minutes) <small className="text-red-500">(required)</small>
          </label>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="mt-1 w-full border border-slate-300 p-2"
            placeholder="Enter duration"
          />

          <label className="mt-4 block font-medium">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="mt-1 w-full border border-slate-300 p-2"
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>

          <button
            onClick={saveService}
            className="mt-4 border border-slate-300 px-3 py-1"
          >
            Save Service
          </button>
        </div>
      )}

      {/* Displays the services returned by the backend */}
      <div className="mt-4">
        {services.map((service) => (
          <div
            key={service.name}
            className="mb-3 border border-slate-200 bg-white p-4"
          >
            <h3 className="font-semibold">{service.name}</h3>
            <p className="mt-1 break-words whitespace-pre-wrap">
              {service.description}
            </p>
            <p className="mt-1">
              Expected duration: {service.expected_duration} minutes
            </p>
            <p className="mt-1">
              Priority: {
              service.priority <=2
                ? 'Low'
                : service.priority >= 4
                  ? 'High'
                  : 'Medium'
              }
            </p>

            <button
              onClick={() => editService(service)}
              className="mt-3 border border-slate-300 px-3 py-1"
            >
              Edit
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ServiceManagement
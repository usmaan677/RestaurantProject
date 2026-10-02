import { useState } from 'react'

function ServiceManagement() {
  const [showForm, setShowForm] = useState(false)
  const [serviceName, setServiceName] = useState('')
  const [description, setDescription] = useState('')
  const [duration, setDuration] = useState('')
  const [priority, setPriority] = useState('Medium')
  const [editingService, setEditingService] = useState('')

  const [services, setServices] = useState([
    {
      name: 'Dine In',
      description: 'Dine in at the restaurant.',
      duration: 30,
      priority: 'Medium',
    },
    {
      name: 'Take Out',
      description: 'Pick up your order at the counter.',
      duration: 10,
      priority: 'Medium',
    },
    {
      name: 'DoorDash',
      description: 'Prepare orders for delivery.',
      duration: 15,
      priority: 'High',
    },
  ])

  function saveService() {
    if (!serviceName || !description || !duration) {
      alert('Please fill in all required fields.')
      return
    }

    const service = {
      name: serviceName,
      description: description,
      duration: duration,
      priority: priority,
    }

    if (editingService) {
      setServices(
        services.map((item) =>
          item.name === editingService ? service : item
        )
      )
    } else {
      setServices([...services, service])
    }

    setShowForm(false)
    setEditingService('')
  }

  function editService(service) {
    setEditingService(service.name)
    setServiceName(service.name)
    setDescription(service.description)
    setDuration(service.duration)
    setPriority(service.priority)
    setShowForm(true)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Service Management</h1>
      <p className="mt-2">Manage services for Downtown Houston.</p>

      <h2 className="mt-6 text-xl font-semibold">Current Services</h2>

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

          <label className="mt-4 block font-medium">Service Name</label>
          <input
            type="text"
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            maxLength={100}
            className="mt-1 w-full border border-slate-300 p-2"
            placeholder="Enter service name"
          />

          <label className="mt-4 block font-medium">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full border border-slate-300 p-2"
            placeholder="Enter service description"
          />

          <label className="mt-4 block font-medium">
            Expected Duration (minutes)
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

      <div className="mt-4">
        {services.map((service) => (
          <div
            key={service.name}
            className="mb-3 border border-slate-200 bg-white p-4"
          >
            <h3 className="font-semibold">{service.name}</h3>
            <p className="mt-1">{service.description}</p>
            <p className="mt-1">
              Expected duration: {service.duration} minutes
            </p>
            <p className="mt-1">Priority: {service.priority}</p>

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
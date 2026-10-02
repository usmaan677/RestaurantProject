import { useState } from 'react'

function AdminDashboard() {
    const [services, setServices] = useState([
  {
    name: 'Dine In',
    queueLength: 8,
    isOpen: true,
  },
  {
    name: 'Take Out',
    queueLength: 4,
    isOpen: true,
  },
  {
    name: 'DoorDash',
    queueLength: 2,
    isOpen: false,
  },
])
  
    return (
    <div>
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      <p className="mt-2">Location: Downtown Houston</p>

      <div className="mt-6">
        <h2 className="text-xl font-semibold">Services</h2>

        <div className="mt-4">
            {services.map((service) => (
                <div className="mb-3 border border-slate-200 bg-white p-4" key={service.name}>
                    <h3 className="font-semibold">{service.name}</h3>
                    <p className="mt-1">Queue length: {service.queueLength}</p>
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
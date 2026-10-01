import { Link } from 'react-router-dom'
import { services, notifications } from '../mockData'

function Dashboard() {
  const currentQueue = services[0]

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
      <p className="mt-2 text-slate-600">Here's what's happening with your orders.</p>

      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-800">Current Queue</h2>
        <p className="mt-1 text-slate-600">
          You are in line for <span className="font-medium">{currentQueue.name}</span> — position #
          {currentQueue.position}, about {currentQueue.waitTime} minutes.
        </p>
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
                <p className="text-sm text-slate-600">{service.waitTime} min wait</p>
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

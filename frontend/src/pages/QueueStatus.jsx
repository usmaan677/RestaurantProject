import { useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
// The queue lists come from the mockData file
import { services } from '../mockData'

function QueueStatus() {
  // JoinQueue sends us the chosen service id. If it is missing, show the first service.
  const location = useLocation()
  const serviceId = location.state?.serviceId ?? services[0].id
  const service = services.find((s) => s.id === serviceId)

  // Becomes true when the user clicks "Leave Queue".
  // It only lives on this page, so it resets when the page reloads.
  const [left, setLeft] = useState(false)

  // Nothing to show if the service wasn't found or the user left
  if (!service || left) {
    return (
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-3xl font-bold text-slate-800">Queue Status</h1>
        <p className="mt-4 text-slate-600">You are not currently in a queue.</p>
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
        <p className="text-lg font-medium text-slate-800">{service.name}</p>
        <p className="mt-2 text-slate-600">Position in queue: #{service.position}</p>
        <p className="text-slate-600">Estimated wait: {service.waitTime} minutes</p>
        <p className="mt-2">
          Status: <span className="font-medium text-slate-800">{service.status}</span>
        </p>
      </div>

      {/* The whole line, in order, filled in from mockData */}
      <div className="mt-6 rounded border border-slate-200 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-800">Who's in line</h2>
        <ol className="mt-2 flex flex-col gap-1">
          {service.queue.map((person, index) => (
            <li
              key={person.id}
              className={person.name === 'You' ? 'font-semibold text-blue-600' : 'text-slate-700'}
            >
              {index + 1}. {person.name}
            </li>
          ))}
        </ol>
      </div>

      <button
        onClick={() => setLeft(true)}
        className="mt-4 rounded border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100"
      >
        Leave Queue
      </button>
    </div>
  )
}

export default QueueStatus

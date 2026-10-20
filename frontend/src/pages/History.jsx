import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function History() {
  const user = JSON.parse(localStorage.getItem('user'))

  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    async function loadHistory() {
      const response = await fetch(`/api/history?email=${encodeURIComponent(user.email)}`)
      setHistory(response.ok ? await response.json() : [])
      setLoading(false)
    }

    loadHistory()
  }, [])

  if (!user) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Queue History</h1>
        <p className="mt-4 text-slate-600">
          Please <Link to="/login" className="text-blue-600 hover:underline">log in</Link> to see your queue history.
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Queue History</h1>
        <p className="mt-4 text-slate-600">Loading...</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-800">Queue History</h1>
      <p className="mt-2 text-slate-600">Queues you've joined in the past.</p>

      <table className="mt-6 w-full border-collapse rounded border border-slate-200 bg-white">
        <thead>
          <tr className="border-b border-slate-200 text-left">
            <th className="px-4 py-2 text-slate-700">Date</th>
            <th className="px-4 py-2 text-slate-700">Service</th>
            <th className="px-4 py-2 text-slate-700">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {history.length === 0 && (
            <tr>
              <td className="px-4 py-2 text-slate-600" colSpan={3}>No queue history yet.</td>
            </tr>
          )}
          {history.map((item) => (
            <tr key={item.id} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-2 text-slate-600">{item.date}</td>
              <td className="px-4 py-2 text-slate-600">{item.service_name}</td>
              <td className="px-4 py-2 text-slate-600">{item.outcome}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default History

import { history } from '../mockData'

function History() {
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
          {history.map((item) => (
            <tr key={item.id} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-2 text-slate-600">{item.date}</td>
              <td className="px-4 py-2 text-slate-600">{item.service}</td>
              <td className="px-4 py-2 text-slate-600">{item.outcome}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default History

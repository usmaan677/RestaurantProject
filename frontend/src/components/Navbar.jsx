import { NavLink } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="flex items-center justify-between bg-white border-b border-slate-200 px-6 py-4">
      <span className="text-lg font-bold text-slate-800">Restaurant Manager</span>

      <div className="flex gap-6">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          Home
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          Dashboard
        </NavLink>
        <NavLink to="/join-queue" className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          Join Queue
        </NavLink>
        <NavLink to="/queue-status" className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          Queue Status
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          History
        </NavLink>
        <NavLink to="/login" className={({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'}>
          Log In
        </NavLink>
      </div>
    </nav>
  )
}

export default Navbar
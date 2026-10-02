import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { FaRegBell } from 'react-icons/fa'
import { notifications } from '../mockData'

function Navbar() {
  // Keeps track of which dropdown is open: 'queue', 'admin', 'bell', or '' (none)
  const [openMenu, setOpenMenu] = useState('')

  // Opens a menu, or closes it if it is already open
  function toggleMenu(menuName) {
    if (openMenu === menuName) {
      setOpenMenu('')
    } else {
      setOpenMenu(menuName)
    }
  }

  // Closes any open menu (used after clicking a link)
  function closeMenu() {
    setOpenMenu('')
  }

  const linkStyle = ({ isActive }) => isActive ? 'font-semibold text-slate-900' : 'text-slate-600 hover:text-slate-900'
  const dropdownLinkStyle = ({ isActive }) => isActive ? 'block px-4 py-2 font-semibold text-slate-900 bg-slate-100' : 'block px-4 py-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900'

  return (
    <nav className="flex items-center justify-between bg-white border-b border-slate-200 px-6 py-4">
      <span className="text-lg font-bold text-slate-800">Restaurant Manager</span>

      <div className="flex items-center gap-6">
        <NavLink to="/" end className={linkStyle} onClick={closeMenu}>
          Dashboard
        </NavLink>

        {/* Queue dropdown */}
        <div className="relative">
          <button onClick={() => toggleMenu('queue')} className="text-slate-600 hover:text-slate-900">
            Queue ▾
          </button>

          {openMenu === 'queue' && (
            <div className="absolute right-0 mt-2 w-44 bg-white border border-slate-200 rounded shadow">
              <NavLink to="/join-queue" className={dropdownLinkStyle} onClick={closeMenu}>
                Join Queue
              </NavLink>
              <NavLink to="/queue-status" className={dropdownLinkStyle} onClick={closeMenu}>
                Queue Status
              </NavLink>
              <NavLink to="/history" className={dropdownLinkStyle} onClick={closeMenu}>
                History
              </NavLink>
            </div>
          )}
        </div>

        {/* Admin dropdown */}
        <div className="relative">
          <button onClick={() => toggleMenu('admin')} className="text-slate-600 hover:text-slate-900">
            Admin ▾
          </button>

          {openMenu === 'admin' && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded shadow">
              <NavLink to="/admin" end className={dropdownLinkStyle} onClick={closeMenu}>
                Admin Dashboard
              </NavLink>
              <NavLink to="/admin/services" className={dropdownLinkStyle} onClick={closeMenu}>
                Admin Services
              </NavLink>
              <NavLink to="/admin-queue" className={dropdownLinkStyle} onClick={closeMenu}>
                Admin Queue
              </NavLink>
            </div>
          )}
        </div>

        <NavLink to="/login" className={linkStyle} onClick={closeMenu}>
          Log In
        </NavLink>

        {/* Notification bell dropdown */}
        <div className="relative">
          <button onClick={() => toggleMenu('bell')} className="relative flex items-center text-slate-600 hover:text-slate-900">
            <FaRegBell size={20} />
            {/* Small red circle showing how many notifications there are */}
            <span className="absolute -top-1 -right-2 rounded-full bg-red-500 px-1.5 text-xs text-white">
              {notifications.length}
            </span>
          </button>

          {openMenu === 'bell' && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded shadow p-4">
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
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar

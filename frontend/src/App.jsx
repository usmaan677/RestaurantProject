import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Register from './pages/Register'
import LogIn from './pages/LogIn'
import Dashboard from './pages/Dashboard'
import JoinQueue from './pages/JoinQueue'
import QueueStatus from './pages/QueueStatus'
import History from './pages/History'

function App() {
  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />
      <main className="max-w-5xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LogIn />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/join-queue" element={<JoinQueue />} />
          <Route path="/queue-status" element={<QueueStatus />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<h1 className="text-2xl">Page not found</h1>} />
        </Routes>
      </main>
    </div>
  )
}

export default App

import { useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import TryModelsPage from './pages/TryModelsPage'
import DashboardLayout from './pages/DashboardLayout'
import FarmerDashboard from './pages/FarmerDashboard'
import MicrofinanceDashboard from './pages/MicrofinanceDashboard'
import AdminDashboard from './pages/AdminDashboard'

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  // Scroll to hash target when URL has a hash (e.g. /#about) so header links work
  useEffect(() => {
    if (location.hash) {
      const id = location.hash.replace('#', '')
      const el = id ? document.getElementById(id) : null
      if (el) {
        const timer = setTimeout(() => {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
        return () => clearTimeout(timer)
      }
    }
  }, [location.pathname, location.hash])

  return (
    <Routes>
      <Route
        path="/"
        element={<LandingPage onLoginToDashboard={(path) => navigate(path)} />}
      />
      <Route path="/try-models" element={<TryModelsPage />} />
      <Route path="/dashboard" element={<DashboardLayout />}>
        <Route path="farmer" element={<FarmerDashboard />} />
        <Route path="microfinance" element={<MicrofinanceDashboard />} />
        <Route path="admin" element={<AdminDashboard />} />
      </Route>
    </Routes>
  )
}

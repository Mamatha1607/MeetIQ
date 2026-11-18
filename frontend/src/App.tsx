
import { Routes, Route, Navigate } from 'react-router-dom'

import PublicLayout from './components/PublicLayout'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import MeetingDetails from './pages/MeetingDetails'
import ComingSoon from './pages/ComingSoon'

export default function App() {
  return (
    <Routes>
      {/* Public website */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      {/* Private application */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/meetings" element={<Dashboard />} />
          <Route path="/meetings/:meetingId" element={<MeetingDetails />} />
          <Route path="/actions" element={<ComingSoon title="Action Items" />} />
          <Route path="/search" element={<ComingSoon title="Meeting Search" />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

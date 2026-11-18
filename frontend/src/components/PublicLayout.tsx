import { Outlet } from 'react-router-dom'
import PublicNavbar from './PublicNavbar'

export default function PublicLayout() {
  return (
    <div className="min-h-dvh bg-[#F3F0FF]">
      <PublicNavbar />
      <Outlet />
    </div>
  )
}

import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  AudioLines,
  LayoutDashboard,
  CalendarDays,
  ListTodo,
  Search,
  Settings,
  Sparkles,
  Menu,
  X,
  Bell,
  ChevronRight,
} from 'lucide-react'

const navigation = [
  {
    to: '/',
    label: 'Dashboard',
    icon: LayoutDashboard,
  },
  {
    to: '/meetings',
    label: 'My Meetings',
    icon: CalendarDays,
  },
  {
    to: '/actions',
    label: 'Action Items',
    icon: ListTodo,
  },
  {
    to: '/search',
    label: 'AI Search',
    icon: Search,
  },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#F8F9FD] text-slate-900">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 flex w-[272px]
          flex-col border-r border-[#E8EAF2] bg-white
          transition-transform duration-300
          lg:translate-x-0
          ${
            sidebarOpen
              ? 'translate-x-0'
              : '-translate-x-full'
          }
        `}
      >
        {/* Logo */}
        <div className="flex h-[92px] items-center justify-between px-7">
          <button
            type="button"
            onClick={() => {
              navigate('/')
              setSidebarOpen(false)
            }}
            className="flex items-center gap-3 text-left"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
              <AudioLines size={25} strokeWidth={2.5} />
            </div>

            <div>
              <h1 className="text-[23px] font-extrabold leading-none tracking-tight text-[#11152E]">
                MeetIQ
              </h1>

              <p className="mt-1 text-[11px] font-medium text-slate-500">
                AI Meeting Intelligence
              </p>
            </div>
          </button>

          <button
            type="button"
            aria-label="Close sidebar"
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav
          aria-label="Main navigation"
          className="mt-9 space-y-2 px-4"
        >
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `
                  flex items-center gap-3.5 rounded-xl
                  px-4 py-3.5 text-[14px] font-semibold
                  transition-all duration-200
                  ${
                    isActive
                      ? 'bg-[#EEECFF] text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-indigo-600'
                  }
                `
              }
            >
              <Icon size={20} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-6 border-t border-slate-100 px-4 pt-5">
          <div
            className="flex cursor-default items-center gap-3.5 rounded-xl px-4 py-3 text-sm font-medium text-slate-400"
            title="Settings coming soon"
          >
            <Settings size={20} />
            <span>Settings</span>
          </div>
        </div>

        {/* Bottom promotional card */}
        <div className="mt-auto p-4">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#8177F9] to-[#4F46E5] p-5 text-white">
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10" />

            <div className="relative">
              <Sparkles size={24} />

              <h3 className="mt-4 text-[17px] font-bold text-white">
                Smarter Meetings
              </h3>

              <p className="mt-2 text-xs leading-5 text-indigo-100">
                Transform your recordings into summaries,
                decisions, and actionable insights.
              </p>

              <button
                type="button"
                onClick={() => {
                  navigate('/meetings')
                  setSidebarOpen(false)
                }}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-3 py-3 text-xs font-bold text-indigo-700 transition hover:bg-indigo-50"
              >
                Explore Meetings
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          <p className="mt-4 text-center text-[11px] text-slate-400">
            MeetIQ · AI Meeting Intelligence
          </p>
        </div>
      </aside>

      {/* Main content */}
      <div className="min-h-screen lg:pl-[272px]">
        {/* Top header */}
        <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-[#E8EAF2] bg-white/95 px-5 backdrop-blur-md sm:px-9">
          <div className="flex items-center gap-4">
            <button
              type="button"
              aria-label="Open navigation"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            >
              <Menu size={23} />
            </button>

            <div>
              <p className="text-sm font-bold text-[#15182D]">
                MeetIQ Workspace
              </p>

              <p className="mt-0.5 text-xs text-slate-400">
                Your meetings, organized.
              </p>
            </div>
          </div>

          {/* Header right */}
          <div className="flex items-center gap-4">
            <div
              title="Notifications coming soon"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-500"
            >
              <Bell size={20} />
            </div>

            <div className="h-8 w-px bg-slate-200" />

            <div
              title="Account settings coming soon"
              className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E9E6FF] text-sm font-bold text-indigo-700"
            >
              M
            </div>
          </div>
        </header>

        {/* Page content */}
        <Outlet />
      </div>
    </div>
  )
}

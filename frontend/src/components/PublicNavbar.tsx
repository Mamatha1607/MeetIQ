
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { AudioLines, Menu, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function PublicNavbar() {
  const { isAuthenticated } = useAuth()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const isLogin = pathname === '/login'
  const isRegister = pathname === '/register'

  return (
    <header className="sticky top-0 z-50 border-b border-indigo-100/60 bg-[#F3F0FF]/95 backdrop-blur-xl">
      <nav className="mx-auto flex h-[84px] max-w-[1400px] items-center justify-between px-5 sm:px-8 lg:px-12">
        <Link
          to="/"
          onClick={() => setMenuOpen(false)}
          className="flex items-center gap-3"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#5848E5] text-white">
            <AudioLines size={26} strokeWidth={2.5} />
          </span>
          <span className="text-[28px] font-extrabold tracking-tight text-[#11152E]">
            Meet<span className="text-[#5848E5]">IQ</span>
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <Link to="/" className="text-base font-medium text-indigo-700 hover:text-indigo-500">
            Home
          </Link>
          <Link to="/#features" className="text-base font-medium text-indigo-700 hover:text-indigo-500">
            Features
          </Link>

          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="rounded-xl bg-[#5848E5] px-6 py-3 font-semibold text-white hover:bg-indigo-700"
            >
              Dashboard
            </Link>
          ) : (
            <>
              {!isLogin && (
                <Link to="/login" className="text-base font-medium text-indigo-700 hover:text-indigo-500">
                  Login
                </Link>
              )}
              {!isRegister && (
                <Link
                  to="/register"
                  className="rounded-xl bg-[#5848E5] px-6 py-3 font-semibold text-white hover:bg-indigo-700"
                >
                  Sign up
                </Link>
              )}
            </>
          )}
        </div>

        <button
          type="button"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(!menuOpen)}
          className="rounded-lg p-2 text-indigo-700 md:hidden"
        >
          {menuOpen ? <X size={25} /> : <Menu size={25} />}
        </button>
      </nav>

      {menuOpen && (
        <div className="flex flex-col gap-4 border-t border-indigo-100 bg-[#F3F0FF] px-6 py-5 md:hidden">
          <Link to="/" onClick={() => setMenuOpen(false)}>Home</Link>
          <Link to="/#features" onClick={() => setMenuOpen(false)}>Features</Link>

          {isAuthenticated ? (
            <Link to="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</Link>
          ) : (
            <>
              {!isLogin && (
                <Link to="/login" onClick={() => setMenuOpen(false)}>Login</Link>
              )}
              {!isRegister && (
                <Link to="/register" onClick={() => setMenuOpen(false)}>Sign up</Link>
              )}
            </>
          )}
        </div>
      )}
    </header>
  )
}

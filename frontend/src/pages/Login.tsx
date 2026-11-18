
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AudioLines, ArrowRight, LockKeyhole, Mail, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const from = location.state?.from?.pathname ?? '/'

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError('Invalid email or password.')
      } else {
        setError('Unable to sign in. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="meetiq-page-enter flex min-h-screen items-center justify-center bg-[#F8F9FD] px-4 py-12">
      <div className="w-full max-w-[440px]">
        <div className="mb-9 flex flex-col items-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-200">
            <AudioLines size={29} strokeWidth={2.4} />
          </div>

          <h1 className="mt-4 text-[30px] font-extrabold tracking-tight text-[#11152E]">
            MeetIQ
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            AI Meeting Intelligence
          </p>
        </div>

        <div className="meetiq-card p-7 shadow-sm sm:p-9">
          <div className="mb-7">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700">
              <Sparkles size={14} />
              Your intelligent workspace
            </div>

            <h2 className="text-[26px] font-bold text-[#11152E]">
              Welcome back
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Sign in to manage your meetings and insights.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-semibold text-slate-700">
                Email address
              </label>

              <div className="relative">
                <Mail size={18} className="pointer-events-none absolute left-4 top-3.5 text-slate-400" />

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="meetiq-input meetiq-input-icon"
                />
              </div>
            </div>

            <div>
  <label
    htmlFor="password"
    className="mb-2 block text-sm font-semibold text-slate-700"
  >
    Password
  </label>

  <div className="relative">
    <LockKeyhole
      size={18}
      className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
    />

    <input
      id="password"
      type="password"
      autoComplete="current-password"
      required
      value={password}
      onChange={(event) => setPassword(event.target.value)}
      placeholder="Enter your password"
      className="meetiq-input meetiq-input-icon"
    />
  </div>
</div>

            {error && (
              <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="meetiq-gradient flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3.5 font-semibold text-white shadow-md shadow-indigo-100 transition hover:opacity-95 disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Sign in'}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          <p className="mt-7 text-center text-sm text-slate-500">
            New to MeetIQ?{' '}
            <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-700">
              Create an account
            </Link>
          </p>
        </div>

        <p className="mt-7 text-center text-xs text-slate-400">
          MeetIQ · Smarter meetings, clearer decisions.
        </p>
      </div>
    </div>
  )
}

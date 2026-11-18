
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import axios from 'axios'

import {
  AudioLines,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  Sparkles,
} from 'lucide-react'

import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (password.length < 12) {
      setError('Password must contain at least 12 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await register({
        email: email.trim(),
        password,
      })

      navigate('/dashboard', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setError('An account with this email already exists.')
      } else if (axios.isAxiosError(err) && err.response?.status === 422) {
        setError('Please check your email address and password.')
      } else {
        setError('Unable to create your account. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-[#F3F0FF] px-4 py-8">

      <div className="meetiq-page-enter w-full max-w-[480px]">

        {/* MeetIQ logo */}
        <div className="mb-7 flex justify-center">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-200">
              <AudioLines size={26} strokeWidth={2.5} />
            </span>

            <span>
              <span className="block text-[28px] font-extrabold leading-none tracking-tight text-[#11152E]">
                Meet<span className="text-indigo-600">IQ</span>
              </span>

              <span className="mt-1 block text-xs font-medium text-slate-500">
                AI Meeting Intelligence
              </span>
            </span>
          </Link>
        </div>

        {/* Registration card */}
        <div className="rounded-[24px] border border-indigo-100 bg-white px-6 py-8 shadow-[0_20px_60px_rgba(79,70,229,0.10)] sm:px-9">

          {/* Header */}
          <div className="text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#EEECFF] px-4 py-2 text-xs font-bold text-indigo-700">
              <Sparkles size={15} />
              Get started with MeetIQ
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-[#11152E]">
              Create your account
            </h1>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Start turning meetings into actionable insights.
            </p>
          </div>

          {/* Registration form */}
          <form
            onSubmit={handleSubmit}
            className="mt-7 space-y-5"
          >

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-semibold text-[#11152E]"
              >
                Email address
              </label>

              <div className="relative">
                <Mail
                  size={19}
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />

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

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-semibold text-[#11152E]"
              >
                Password
              </label>

              <div className="relative">
                <LockKeyhole
                  size={19}
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  minLength={12}
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Minimum 12 characters"
                  className="meetiq-input meetiq-input-icon meetiq-input-password"
                />

                <button
                  type="button"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-indigo-600"
                >
                  {showPassword
                    ? <EyeOff size={19} />
                    : <Eye size={19} />}
                </button>
              </div>

              <p className="mt-1.5 text-xs text-slate-400">
                Use at least 12 characters.
              </p>
            </div>

            {/* Confirm password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="mb-2 block text-sm font-semibold text-[#11152E]"
              >
                Confirm password
              </label>

              <div className="relative">
                <LockKeyhole
                  size={19}
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="Re-enter your password"
                  className="meetiq-input meetiq-input-icon meetiq-input-password"
                />

                <button
                  type="button"
                  aria-label={
                    showConfirmPassword
                      ? 'Hide confirmation password'
                      : 'Show confirmation password'
                  }
                  onClick={() =>
                    setShowConfirmPassword((value) => !value)
                  }
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-indigo-600"
                >
                  {showConfirmPassword
                    ? <EyeOff size={19} />
                    : <Eye size={19} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <p
                role="alert"
                className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600"
              >
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="meetiq-gradient flex w-full items-center justify-center gap-3 rounded-xl px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-200 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Creating account...' : 'Create account'}

              {!loading && <ArrowRight size={19} />}
            </button>
          </form>

          {/* Login link */}
          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-bold text-indigo-600 hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>

        {/* Back to homepage */}
        <div className="mt-6 text-center">
          <Link
            to="/"
            className="text-sm font-medium text-slate-500 transition hover:text-indigo-600"
          >
            ← Back to homepage
          </Link>
        </div>

        <p className="mt-5 text-center text-xs text-slate-400">
          MeetIQ · AI Meeting Intelligence
        </p>
      </div>
    </main>
  )
}


import { useMemo, useState } from 'react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  Link,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import axios from 'axios'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileAudio,
  Plus,
  Search,
  Trash2,
  Pencil,
  ArrowUpRight,
  X,
  LoaderCircle,
  Sparkles,
  ChevronRight,
  SlidersHorizontal,
  Mic2,
  FolderOpen,
} from 'lucide-react'

import {
  createMeeting,
  deleteMeeting,
  getMeetings,
  updateMeeting,
} from '../services/meetings'

import type { Meeting } from '../types/meeting'
import StatusBadge from '../components/StatusBadge'

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      return detail
    }

    return error.message
  }

  return 'Something went wrong. Please try again.'
}

function formatDate(date: string): string {
  const parsed = new Date(date)

  if (Number.isNaN(parsed.getTime())) {
    return 'Unknown date'
  }

  return parsed.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function Dashboard() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const isOverview = pathname !== '/meetings'

  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  const [modal, setModal] = useState<
    'create' | 'edit' | null
  >(null)

  const [editing, setEditing] = useState<Meeting | null>(
    null
  )

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  // Fetch meetings from FastAPI
  const {
    data: meetings = [],
    isPending,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['meetings'],
    queryFn: getMeetings,
    refetchInterval: 10000,
  })

  // Create meeting
  const createMutation = useMutation({
    mutationFn: createMeeting,

    onSuccess: async (meeting) => {
      await queryClient.invalidateQueries({
        queryKey: ['meetings'],
      })

      setModal(null)
      navigate(`/meetings/${meeting.id}`)
    },

    onError: (err) => {
      setError(getErrorMessage(err))
    },
  })

  // Edit meeting
  const updateMutation = useMutation({
    mutationFn: ({
      id,
      title,
      description,
    }: {
      id: string
      title: string
      description: string
    }) =>
      updateMeeting(id, {
        title,
        description,
      }),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['meetings'],
      })

      setModal(null)
      setEditing(null)
    },

    onError: (err) => {
      setError(getErrorMessage(err))
    },
  })

  // Delete meeting
  const deleteMutation = useMutation({
    mutationFn: deleteMeeting,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['meetings'],
      })
    },

    onError: (err) => {
      window.alert(getErrorMessage(err))
    },
  })

  // Filter and sort meetings
  const filteredMeetings = useMemo(() => {
    const searchText = search.trim().toLowerCase()

    return meetings
      .filter((meeting) => {
        const matchesStatus =
          filter === 'all' ||
          meeting.status === filter

        const matchesSearch =
          meeting.title
            .toLowerCase()
            .includes(searchText) ||
          (meeting.description ?? '')
            .toLowerCase()
            .includes(searchText)

        return matchesStatus && matchesSearch
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime()
      )
  }, [meetings, search, filter])

  // Dashboard statistics
  const stats = [
    {
      label: 'Total Meetings',
      value: meetings.length,
      icon: CalendarDays,
      color: 'text-indigo-600',
      background: 'bg-indigo-50',
    },
    {
      label: 'Completed',
      value: meetings.filter(
        (meeting) => meeting.status === 'completed'
      ).length,
      icon: CheckCircle2,
      color: 'text-emerald-600',
      background: 'bg-emerald-50',
    },
    {
      label: 'In Progress',
      value: meetings.filter(
        (meeting) =>
          meeting.status === 'queued' ||
          meeting.status === 'processing'
      ).length,
      icon: Clock3,
      color: 'text-amber-600',
      background: 'bg-amber-50',
    },
    {
      label: 'Ready to Process',
      value: meetings.filter(
        (meeting) => meeting.status === 'uploaded'
      ).length,
      icon: FileAudio,
      color: 'text-violet-600',
      background: 'bg-violet-50',
    },
  ]

  function openCreateModal() {
    setEditing(null)
    setTitle('')
    setDescription('')
    setError('')
    createMutation.reset()
    setModal('create')
  }

  function openEditModal(meeting: Meeting) {
    setEditing(meeting)
    setTitle(meeting.title)
    setDescription(meeting.description ?? '')
    setError('')
    updateMutation.reset()
    setModal('edit')
  }

  function closeModal() {
    if (
      createMutation.isPending ||
      updateMutation.isPending
    ) {
      return
    }

    setModal(null)
    setEditing(null)
    setError('')
  }

  function handleDelete(meeting: Meeting) {
    if (
      meeting.status === 'queued' ||
      meeting.status === 'processing'
    ) {
      return
    }

    const confirmed = window.confirm(
      `Delete "${meeting.title}"? This cannot be undone.`
    )

    if (confirmed) {
      deleteMutation.mutate(meeting.id)
    }
  }

  function handleSubmit(
    event: React.SubmitEvent<HTMLFormElement>
  ) {
    event.preventDefault()
    setError('')

    if (!title.trim()) {
      setError('Meeting title is required.')
      return
    }

    if (modal === 'create') {
      createMutation.mutate({
        title: title.trim(),
        description: description.trim(),
      })
    } else if (modal === 'edit' && editing) {
      updateMutation.mutate({
        id: editing.id,
        title: title.trim(),
        description: description.trim(),
      })
    }
  }

  return (
    <main className="meetiq-page-enter mx-auto max-w-[1500px] px-5 py-8 text-slate-900 sm:px-9 lg:px-11">
      {/* PAGE HEADER */}
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div>
          <p className="mb-2 text-sm font-semibold text-indigo-600">
            {isOverview
              ? 'Workspace / Dashboard'
              : 'Workspace / My Meetings'}
          </p>

          <h1 className="text-[30px] font-extrabold tracking-tight text-[#15182D] sm:text-[36px]">
            {isOverview
              ? 'Your meetings'
              : 'My Meetings'}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            {isOverview
              ? 'Manage your recordings and turn conversations into actionable insights.'
              : 'All your conversations, organized in one place.'}
          </p>
        </div>

        <button
          type="button"
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-indigo-700"
        >
          <Plus size={19} />
          New Meeting
        </button>
      </div>

      {/* DASHBOARD ONLY */}
      {isOverview && (
        <>
          {/* STATISTICS */}
          <div className="mt-9 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon

              return (
                <div
                  key={stat.label}
                  className="rounded-2xl border border-[#E8EAF2] bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-[13px] font-semibold text-slate-500">
                      {stat.label}
                    </p>

                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl ${stat.background} ${stat.color}`}
                    >
                      <Icon size={22} />
                    </div>
                  </div>

                  <p className="mt-4 text-[34px] font-extrabold tracking-tight text-[#15182D]">
                    {isPending ? '—' : stat.value}
                  </p>
                </div>
              )
            })}
          </div>

          {/* PURPLE BANNER */}
          <div className="relative mt-8 overflow-hidden rounded-[20px] bg-gradient-to-r from-[#4F46E5] via-[#6254EE] to-[#8174F8] px-7 py-8 text-white shadow-sm sm:px-9">
            <div className="absolute -right-12 -top-20 h-60 w-60 rounded-full border-[35px] border-white/10" />

            <div className="absolute bottom-[-90px] right-32 h-48 w-48 rounded-full bg-white/5" />

            <div className="relative flex flex-wrap items-center justify-between gap-5">
              <div className="flex items-start gap-4">
                <div className="hidden rounded-2xl bg-white/15 p-3 sm:block">
                  <Sparkles size={27} />
                </div>

                <div>
                  <h2 className="text-[22px] font-extrabold tracking-tight text-white">
                    Make every meeting count.
                  </h2>

                  <p className="mt-2 max-w-xl text-sm leading-6 text-indigo-100">
                    Upload a recording and let MeetIQ
                    transform your conversations into
                    meaningful insights.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={openCreateModal}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-indigo-700 transition hover:bg-indigo-50"
              >
                <Plus size={18} />
                Upload Meeting
              </button>
            </div>
          </div>
        </>
      )}

      {/* MEETINGS SECTION */}
      <section className="mt-9 overflow-hidden rounded-2xl border border-[#E8EAF2] bg-white shadow-sm">
        {/* SECTION HEADER */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-6">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-[19px] font-bold text-[#15182D]">
                {isOverview
                  ? 'Recent Meetings'
                  : 'All Meetings'}
              </h2>

              {!isPending && !isError && (
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-bold text-indigo-600">
                  {filteredMeetings.length}
                </span>
              )}
            </div>

            <p className="mt-1 text-xs text-slate-400">
              {isOverview
                ? 'Your latest meeting recordings'
                : 'Browse and manage your recordings'}
            </p>
          </div>

          <div className="flex w-full flex-wrap items-center gap-3 sm:w-auto">
            {/* SEARCH */}
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-[#FAFBFF] px-3.5 sm:flex-none">
              <Search
                size={18}
                className="shrink-0 text-slate-400"
              />

              <input
                type="search"
                aria-label="Search meetings"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search meetings..."
                className="w-full bg-transparent py-3 text-sm text-slate-700 outline-none sm:w-48"
              />
            </div>

            {/* FILTER */}
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3">
              <SlidersHorizontal
                size={16}
                className="text-slate-400"
              />

              <select
                aria-label="Filter by status"
                value={filter}
                onChange={(event) =>
                  setFilter(event.target.value)
                }
                className="max-w-36 bg-transparent py-3 text-sm font-medium text-slate-600 outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="created">Created</option>
                <option value="uploaded">Uploaded</option>
                <option value="queued">Queued</option>
                <option value="processing">
                  Processing
                </option>
                <option value="completed">
                  Completed
                </option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* LOADING */}
        {isPending ? (
          <div
            role="status"
            className="flex items-center justify-center gap-3 py-20 text-sm text-slate-500"
          >
            <LoaderCircle
              size={22}
              className="animate-spin text-indigo-600"
            />
            Loading meetings...
          </div>
        ) : isError ? (
          /* ERROR */
          <div className="py-20 text-center">
            <p className="font-medium text-red-600">
              Unable to load meetings.
            </p>

            <button
              type="button"
              onClick={() => void refetch()}
              className="mt-3 text-sm font-semibold text-indigo-600 hover:underline"
            >
              Try Again
            </button>
          </div>
        ) : filteredMeetings.length === 0 ? (
          /* EMPTY STATE */
          <div className="flex flex-col items-center px-5 py-20 text-center">
            <div className="rounded-2xl bg-indigo-50 p-5">
              <FolderOpen
                size={35}
                className="text-indigo-400"
              />
            </div>

            <h3 className="mt-5 text-lg font-bold text-slate-900">
              No meetings found
            </h3>

            <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
              {search || filter !== 'all'
                ? 'Try adjusting your search or status filter.'
                : 'Create your first meeting to start capturing insights.'}
            </p>

            {!search && filter === 'all' && (
              <button
                type="button"
                onClick={openCreateModal}
                className="mt-6 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white hover:bg-indigo-700"
              >
                Create Meeting
              </button>
            )}
          </div>
        ) : (
          <>
            {/* TABLE HEADER */}
            <div className="hidden grid-cols-[minmax(0,1fr)_130px_125px_125px] gap-4 border-b border-slate-100 bg-[#FBFCFF] px-6 py-4 text-xs font-bold uppercase tracking-wide text-slate-400 lg:grid">
              <span>Meeting</span>
              <span>Date</span>
              <span>Status</span>
              <span className="text-right">Actions</span>
            </div>

            {/* MEETING ROWS */}
            <div className="divide-y divide-slate-100">
              {filteredMeetings.map((meeting) => {
                const cannotDelete =
                  meeting.status === 'queued' ||
                  meeting.status === 'processing'

                const isDeleting =
                  deleteMutation.isPending &&
                  deleteMutation.variables === meeting.id

                return (
                  <div
                    key={meeting.id}
                    className="grid grid-cols-1 items-center gap-4 px-6 py-5 transition-colors hover:bg-[#FAFAFF] lg:grid-cols-[minmax(0,1fr)_130px_125px_125px]"
                  >
                    {/* MEETING NAME */}
                    <div className="flex min-w-0 items-center gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                        <Mic2 size={23} />
                      </div>

                      <div className="min-w-0">
                        <Link
                          to={`/meetings/${meeting.id}`}
                          className="block truncate text-sm font-bold text-[#1B1D32] transition hover:text-indigo-600"
                        >
                          {meeting.title}
                        </Link>

                        <p className="mt-1 truncate text-xs text-slate-400">
                          {meeting.description ||
                            'Meeting recording'}
                        </p>
                      </div>
                    </div>

                    {/* DATE */}
                    <div className="text-sm text-slate-500">
                      {formatDate(meeting.created_at)}
                    </div>

                    {/* STATUS */}
                    <div>
                      <StatusBadge
                        status={meeting.status}
                      />
                    </div>

                    {/* ACTIONS */}
                    <div className="flex items-center gap-1 lg:justify-end">
                      <button
                        type="button"
                        title="Edit meeting"
                        aria-label={`Edit ${meeting.title}`}
                        onClick={() =>
                          openEditModal(meeting)
                        }
                        className="rounded-lg p-2 text-slate-400 transition hover:bg-indigo-50 hover:text-indigo-600"
                      >
                        <Pencil size={17} />
                      </button>

                      <button
                        type="button"
                        title={
                          cannotDelete
                            ? 'Cannot delete while processing'
                            : 'Delete meeting'
                        }
                        aria-label={`Delete ${meeting.title}`}
                        disabled={
                          deleteMutation.isPending ||
                          cannotDelete
                        }
                        onClick={() =>
                          handleDelete(meeting)
                        }
                        className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-30"
                      >
                        {isDeleting ? (
                          <LoaderCircle
                            size={17}
                            className="animate-spin"
                          />
                        ) : (
                          <Trash2 size={17} />
                        )}
                      </button>

                      <Link
                        to={`/meetings/${meeting.id}`}
                        title="Open meeting"
                        aria-label={`Open ${meeting.title}`}
                        className="rounded-lg p-2 text-slate-400 transition hover:bg-indigo-50 hover:text-indigo-600"
                      >
                        <ArrowUpRight size={18} />
                      </Link>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* FOOTER */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-[#FCFCFF] px-6 py-4">
              <p className="text-xs text-slate-400">
                Showing {filteredMeetings.length} of{' '}
                {meetings.length} meetings
              </p>

              {isOverview && (
                <Link
                  to="/meetings"
                  className="inline-flex items-center gap-1 text-sm font-bold text-indigo-600 hover:text-indigo-700"
                >
                  View All Meetings
                  <ChevronRight size={17} />
                </Link>
              )}
            </div>
          </>
        )}
      </section>

      {/* CREATE / EDIT MODAL */}
      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-[3px]"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeModal()
            }
          }}
        >
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-lg rounded-[22px] bg-white p-7 shadow-2xl sm:p-8"
          >
            {/* MODAL HEADER */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="mb-4 inline-flex rounded-xl bg-indigo-50 p-3 text-indigo-600">
                  {modal === 'create' ? (
                    <Plus size={23} />
                  ) : (
                    <Pencil size={23} />
                  )}
                </div>

                <h2 className="text-[23px] font-extrabold text-[#15182D]">
                  {modal === 'create'
                    ? 'Create New Meeting'
                    : 'Edit Meeting'}
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  {modal === 'create'
                    ? 'Give your meeting a name to get started.'
                    : 'Update your meeting details.'}
                </p>
              </div>

              <button
                type="button"
                aria-label="Close modal"
                onClick={closeModal}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
              >
                <X size={21} />
              </button>
            </div>

            {/* TITLE */}
            <label className="mt-7 block text-sm font-semibold text-slate-700">
              Meeting Title

              <input
                autoFocus
                type="text"
                required
                maxLength={255}
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                placeholder="e.g. Weekly Engineering Sync"
                className="mt-2 block w-full rounded-xl border border-slate-200 px-4 py-3 text-sm font-normal text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </label>

            {/* DESCRIPTION */}
            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Description
              <span className="ml-1 font-normal text-slate-400">
                (optional)
              </span>

              <textarea
                rows={4}
                maxLength={2000}
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                placeholder="What is this meeting about?"
                className="mt-2 block w-full resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm font-normal text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </label>

            {/* ERROR MESSAGE */}
            {error && (
              <p
                role="alert"
                className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600"
              >
                {error}
              </p>
            )}

            {/* MODAL BUTTONS */}
            <div className="mt-8 flex justify-end gap-3">
              <button
                type="button"
                onClick={closeModal}
                disabled={
                  createMutation.isPending ||
                  updateMutation.isPending
                }
                className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={
                  createMutation.isPending ||
                  updateMutation.isPending
                }
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createMutation.isPending ||
                updateMutation.isPending ? (
                  <>
                    <LoaderCircle
                      size={17}
                      className="animate-spin"
                    />
                    Saving...
                  </>
                ) : modal === 'create' ? (
                  <>
                    <Plus size={18} />
                    Create Meeting
                  </>
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  )
}

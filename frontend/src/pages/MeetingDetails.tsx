
import { useRef, useState } from 'react'
import type {
  ChangeEvent,
  DragEvent,
  ReactNode,
} from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import axios from 'axios'
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  CloudUpload,
  FileAudio,
  FileText,
  LoaderCircle,
  Sparkles,
  Upload,
  X,
  ListTodo,
  MessageSquareText,
  AlertCircle,
  CalendarDays,
  Clock3,
  Lightbulb,
  PlayCircle,
  RotateCcw,
} from 'lucide-react'

import {
  getMeeting,
  getTranscript,
  getInsights,
  processMeeting,
  uploadMeetingFile,
} from '../services/meetings'
import StatusBadge from '../components/StatusBadge'

const FILE_LIMIT = 100 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['mp3', 'wav', 'mp4', 'mpeg']

type Tab = 'summary' | 'transcript' | 'actions' | 'decisions'

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    return typeof detail === 'string'
      ? detail
      : error.message
  }

  return 'An unexpected error occurred.'
}

function asObject(value: unknown): Record<string, unknown> {
  return value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function pick(
  object: Record<string, unknown>,
  keys: string[]
): unknown {
  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) {
      return object[key]
    }
  }

  return undefined
}

function renderValue(value: unknown): ReactNode {
  if (
    value === undefined ||
    value === null ||
    value === ''
  ) {
    return (
      <span className="text-slate-400">
        Not available yet.
      </span>
    )
  }

  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value)
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return (
        <span className="text-slate-400">
          None identified.
        </span>
      )
    }

    return (
      <div className="space-y-3">
        {value.map((item, index) => (
          <div
            key={index}
            className="flex items-start gap-3 rounded-xl border border-slate-100 bg-[#FBFCFF] p-4"
          >
            <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-600">
              {index + 1}
            </div>

            <div className="min-w-0 flex-1 text-sm leading-7 text-slate-700">
              {renderValue(item)}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (typeof value === 'object') {
    return (
      <div className="space-y-3">
        {Object.entries(value as Record<string, unknown>).map(
          ([key, item]) => (
            <div key={key}>
              <span className="font-semibold capitalize text-slate-800">
                {key.replace(/_/g, ' ')}:{' '}
              </span>
              {renderValue(item)}
            </div>
          )
        )}
      </div>
    )
  }

  return String(value)
}

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown date'
  }

  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function MeetingDetails() {
  const { meetingId } = useParams()
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(
    null
  )
  const [dragging, setDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('summary')

  // Fetch meeting details
  const meetingQuery = useQuery({
    queryKey: ['meeting', meetingId],
    queryFn: () => getMeeting(meetingId!),
    enabled: Boolean(meetingId),
    refetchInterval: (query) =>
      ['queued', 'processing'].includes(
        query.state.data?.status ?? ''
      )
        ? 3000
        : false,
  })

  const meeting = meetingQuery.data
  const isCompleted = meeting?.status === 'completed'

  // Upload recording
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      uploadMeetingFile(
        meetingId!,
        file,
        setUploadProgress
      ),

    onSuccess: async () => {
      setSelectedFile(null)
      setUploadSuccess(true)

      if (fileInput.current) {
        fileInput.current.value = ''
      }

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['meeting', meetingId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['meetings'],
        }),
      ])
    },

    onError: (error) => {
      setUploadError(getErrorMessage(error))
    },
  })

  // Start AI processing
  const processMutation = useMutation({
    mutationFn: () => processMeeting(meetingId!),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['meeting', meetingId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['meetings'],
        }),
      ])
    },
  })

  // Fetch transcript after processing completes
  const transcriptQuery = useQuery({
    queryKey: ['transcript', meetingId],
    queryFn: () => getTranscript(meetingId!),
    enabled: Boolean(meetingId) && isCompleted,
    retry: 1,
  })

  // Fetch AI insights after processing completes
  const insightsQuery = useQuery({
    queryKey: ['insights', meetingId],
    queryFn: () => getInsights(meetingId!),
    enabled: Boolean(meetingId) && isCompleted,
    retry: 1,
  })

  function selectFile(file?: File) {
    if (!file) return

    setUploadError('')
    setUploadSuccess(false)
    setUploadProgress(0)

    const extension = file.name
      .split('.')
      .pop()
      ?.toLowerCase()

    if (
      !extension ||
      !ALLOWED_EXTENSIONS.includes(extension)
    ) {
      setSelectedFile(null)
      setUploadError(
        'Please select an MP3, WAV, MP4, or MPEG file.'
      )
      return
    }

    if (file.size === 0 || file.size > FILE_LIMIT) {
      setSelectedFile(null)
      setUploadError(
        'File must be larger than 0 bytes and no more than 100 MB.'
      )
      return
    }

    setSelectedFile(file)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)

    if (
      meeting?.status === 'created' &&
      !uploadMutation.isPending
    ) {
      selectFile(event.dataTransfer.files[0])
    }
  }

  function handleUpload() {
    if (!selectedFile) return

    setUploadError('')
    setUploadSuccess(false)
    uploadMutation.mutate(selectedFile)
  }

  // Loading state
  if (meetingQuery.isPending) {
    return (
      <div
        role="status"
        className="flex min-h-[60vh] items-center justify-center gap-3 text-slate-500"
      >
        <LoaderCircle
          className="animate-spin text-indigo-600"
        />
        Loading meeting...
      </div>
    )
  }

  // Error state
  if (meetingQuery.isError || !meeting) {
    return (
      <div className="px-5 py-20 text-center">
        <AlertCircle
          size={36}
          className="mx-auto text-red-500"
        />

        <h2 className="mt-4 text-lg font-bold text-slate-900">
          Could not load meeting
        </h2>

        <button
          type="button"
          onClick={() => void meetingQuery.refetch()}
          className="mt-4 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white"
        >
          Try Again
        </button>
      </div>
    )
  }

  // Normalize possible AI insight response shapes
  const insightData = asObject(insightsQuery.data)

  const nestedData = asObject(
    pick(insightData, ['insights', 'result', 'data'])
  )

  const insightSource =
    Object.keys(nestedData).length > 0
      ? nestedData
      : insightData

  const summary = pick(insightSource, [
    'summary',
    'meeting_summary',
    'executive_summary',
    'overview',
  ])

  const keyPoints = pick(insightSource, [
    'key_points',
    'key_takeaways',
    'highlights',
  ])

  const actionItems = pick(insightSource, [
    'action_items',
    'actionItems',
    'tasks',
  ])

  const decisions = pick(insightSource, [
    'decisions',
    'key_decisions',
  ])

  const transcriptText = transcriptQuery.data?.text

  // Progress steps reflect actual meeting status
  const steps = [
    {
      label: 'Created',
      description: 'Meeting created',
      completed: true,
    },
    {
      label: 'Uploaded',
      description: 'Recording added',
      completed: [
        'uploaded',
        'queued',
        'processing',
        'completed',
        'failed',
      ].includes(meeting.status),
    },
    {
      label: 'Processing',
      description: 'AI analysis',
      completed: meeting.status === 'completed',
      active: ['queued', 'processing'].includes(
        meeting.status
      ),
    },
    {
      label: 'Insights',
      description: 'Results ready',
      completed: meeting.status === 'completed',
    },
  ]

  const tabs = [
    {
      id: 'summary' as const,
      label: 'AI Summary',
      icon: Sparkles,
    },
    {
      id: 'transcript' as const,
      label: 'Transcript',
      icon: FileText,
    },
    {
      id: 'actions' as const,
      label: 'Action Items',
      icon: ListTodo,
    },
    {
      id: 'decisions' as const,
      label: 'Decisions',
      icon: Lightbulb,
    },
  ]

  return (
    <main className="meetiq-page-enter mx-auto max-w-[1400px] px-5 py-8 sm:px-9 lg:px-11">
      {/* BACK LINK */}
      <Link
        to="/meetings"
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-indigo-600"
      >
        <ArrowLeft size={17} />
        Back to My Meetings
      </Link>

      {/* MEETING HEADER */}
      <div className="mt-7 flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm font-semibold text-indigo-600">
            Meeting Details
          </p>

          <h1 className="mt-2 text-[30px] font-extrabold tracking-tight text-[#15182D] sm:text-[36px]">
            {meeting.title}
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
            {meeting.description ||
              'Manage your recording and explore AI-powered meeting insights.'}
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-2">
              <CalendarDays size={15} />
              {formatDate(meeting.created_at)}
            </span>

            <span className="flex items-center gap-2">
              <Clock3 size={15} />
              {meeting.status === 'completed'
                ? 'Analysis completed'
                : 'Meeting workspace'}
            </span>
          </div>
        </div>

        <StatusBadge status={meeting.status} />
      </div>

      {/* PROGRESS TRACKER */}
      <section className="mt-8 rounded-2xl border border-[#E8EAF2] bg-white px-5 py-7 shadow-sm sm:px-8">
        <div className="mb-7 flex items-center justify-between">
          <h2 className="text-base font-bold text-[#15182D]">
            Meeting Progress
          </h2>

          <span className="text-xs font-semibold capitalize text-slate-400">
            {meeting.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
          {steps.map((step, index) => (
            <div
              key={step.label}
              className="flex items-start gap-3"
            >
              <div
                className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold
                  ${
                    step.completed
                      ? 'border-indigo-600 bg-indigo-600 text-white'
                      : step.active
                        ? 'border-indigo-600 bg-indigo-50 text-indigo-600'
                        : 'border-slate-200 bg-white text-slate-400'
                  }
                `}
              >
                {step.completed ? (
                  <Check size={19} />
                ) : step.active ? (
                  <LoaderCircle
                    size={18}
                    className="animate-spin"
                  />
                ) : (
                  index + 1
                )}
              </div>

              <div>
                <p
                  className={`text-sm font-bold ${
                    step.completed || step.active
                      ? 'text-slate-900'
                      : 'text-slate-400'
                  }`}
                >
                  {step.label}
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* RECORDING SECTION */}
      <section className="mt-7 rounded-2xl border border-[#E8EAF2] bg-white p-6 shadow-sm sm:p-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <FileAudio size={24} />
          </div>

          <div>
            <h2 className="text-lg font-bold text-[#15182D]">
              Meeting Recording
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {meeting.status === 'created'
                ? 'Upload your audio or video recording.'
                : 'Your recording has been submitted for analysis.'}
            </p>
          </div>
        </div>

        {meeting.status === 'created' ? (
          <>
            {/* DROP ZONE */}
            <div
              role="button"
              tabIndex={0}
              aria-label="Select recording"
              onClick={() => {
                if (!uploadMutation.isPending) {
                  fileInput.current?.click()
                }
              }}
              onKeyDown={(event) => {
                if (
                  event.key === 'Enter' ||
                  event.key === ' '
                ) {
                  event.preventDefault()

                  if (!uploadMutation.isPending) {
                    fileInput.current?.click()
                  }
                }
              }}
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`
                mt-7 cursor-pointer rounded-2xl border-2 border-dashed px-5 py-12 text-center transition
                ${
                  dragging
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-[#DDE1EE] bg-[#FAFBFF] hover:border-indigo-400'
                }
                ${
                  uploadMutation.isPending
                    ? 'pointer-events-none opacity-60'
                    : ''
                }
              `}
            >
              <input
                ref={fileInput}
                type="file"
                accept=".mp3,.wav,.mp4,.mpeg"
                className="hidden"
                onChange={(
                  event: ChangeEvent<HTMLInputElement>
                ) =>
                  selectFile(event.target.files?.[0])
                }
              />

              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600">
                <CloudUpload size={31} />
              </div>

              <h3 className="mt-5 text-base font-bold text-slate-900">
                Drag and drop your recording here
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                or click to browse your files
              </p>

              <p className="mt-4 text-xs text-slate-400">
                MP3, WAV, MP4, MPEG · Maximum 100 MB
              </p>
            </div>

            {/* SELECTED FILE */}
            {selectedFile && (
              <div className="mt-5 flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4">
                <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600">
                  <FileAudio size={22} />
                </div>

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-slate-900">
                    {selectedFile.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    {(
                      selectedFile.size /
                      1024 /
                      1024
                    ).toFixed(2)}{' '}
                    MB
                  </p>
                </div>

                <button
                  type="button"
                  aria-label="Remove selected file"
                  disabled={uploadMutation.isPending}
                  onClick={() => {
                    setSelectedFile(null)

                    if (fileInput.current) {
                      fileInput.current.value = ''
                    }
                  }}
                  className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                >
                  <X size={19} />
                </button>
              </div>
            )}

            {/* UPLOAD PROGRESS */}
            {uploadMutation.isPending && (
              <div className="mt-5">
                <div className="mb-2 flex justify-between text-xs font-semibold text-slate-600">
                  <span>Uploading recording...</span>
                  <span>{uploadProgress}%</span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-indigo-600 transition-all"
                    style={{
                      width: `${uploadProgress}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {uploadError && (
              <p
                role="alert"
                className="mt-4 text-sm text-red-600"
              >
                {uploadError}
              </p>
            )}

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                disabled={
                  !selectedFile ||
                  uploadMutation.isPending
                }
                onClick={handleUpload}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {uploadMutation.isPending ? (
                  <LoaderCircle
                    size={18}
                    className="animate-spin"
                  />
                ) : (
                  <Upload size={18} />
                )}

                {uploadMutation.isPending
                  ? 'Uploading...'
                  : 'Upload Recording'}
              </button>
            </div>
          </>
        ) : (
          /* UPLOADED RECORDING STATE */
          <div className="mt-7 flex flex-wrap items-center gap-4 rounded-2xl border border-emerald-100 bg-[#F5FCF8] p-5">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
              <FileAudio size={24} />
            </div>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-900">
                Recording uploaded successfully
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Current status:{' '}
                <span className="font-semibold capitalize">
                  {meeting.status}
                </span>
              </p>
            </div>

            <CheckCircle2
              size={22}
              className="text-emerald-600"
            />
          </div>
        )}

        {uploadSuccess && (
          <p className="mt-4 text-sm font-medium text-emerald-600">
            Your recording is ready for processing.
          </p>
        )}
      </section>

      {/* AI PROCESSING */}
      <section className="mt-7 rounded-2xl border border-[#E8EAF2] bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
              <Sparkles size={24} />
            </div>

            <div>
              <h2 className="text-lg font-bold text-[#15182D]">
                AI Processing
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Generate transcripts and intelligent insights.
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={
              meeting.status !== 'uploaded' ||
              processMutation.isPending
            }
            onClick={() => processMutation.mutate()}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {processMutation.isPending ? (
              <LoaderCircle
                size={18}
                className="animate-spin"
              />
            ) : (
              <Sparkles size={18} />
            )}

            {processMutation.isPending
              ? 'Starting...'
              : 'Start AI Processing'}
          </button>
        </div>

        {/* QUEUED / PROCESSING */}
        {['queued', 'processing'].includes(
          meeting.status
        ) && (
          <div
            role="status"
            className="mt-6 flex items-center gap-3 rounded-xl bg-indigo-50 p-5 text-sm font-medium text-indigo-700"
          >
            <LoaderCircle
              size={20}
              className="shrink-0 animate-spin"
            />

            {meeting.status === 'queued'
              ? 'Your recording is queued and waiting for an available worker.'
              : 'MeetIQ is transcribing and analyzing your recording.'}
          </div>
        )}

        {/* COMPLETED */}
        {isCompleted && (
          <div className="mt-6 flex items-center gap-3 rounded-xl bg-emerald-50 p-5 text-sm font-medium text-emerald-700">
            <CheckCircle2
              size={20}
              className="shrink-0"
            />

            AI processing completed. Your results are ready below.
          </div>
        )}

        {/* FAILED */}
        {meeting.status === 'failed' && (
          <div
            role="alert"
            className="mt-6 flex items-start gap-3 rounded-xl bg-red-50 p-5 text-sm text-red-700"
          >
            <AlertCircle
              size={20}
              className="shrink-0"
            />

            <span>
              {meeting.error_message ||
                'Meeting processing failed.'}
            </span>
          </div>
        )}

        {processMutation.isError && (
          <p
            role="alert"
            className="mt-4 text-sm text-red-600"
          >
            {getErrorMessage(processMutation.error)}
          </p>
        )}
      </section>

      {/* AI INSIGHTS */}
      <section className="mt-7 overflow-hidden rounded-2xl border border-[#E8EAF2] bg-white shadow-sm">
        {/* TABS */}
        <div className="flex flex-wrap gap-2 border-b border-slate-100 px-5 py-4 sm:px-7">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`
                inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition
                ${
                  activeTab === id
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }
              `}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </div>

        {/* TAB CONTENT */}
        <div className="min-h-[300px] p-6 sm:p-8">
          {!isCompleted ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-2xl bg-indigo-50 p-5">
                <MessageSquareText
                  size={34}
                  className="text-indigo-400"
                />
              </div>

              <h3 className="mt-5 text-lg font-bold text-slate-900">
                Your AI insights will appear here
              </h3>

              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                Upload a meeting recording and complete AI
                processing to view its summary, transcript,
                action items, and decisions.
              </p>
            </div>
          ) : activeTab === 'transcript' ? (
            <div>
              <div className="mb-6 flex items-center gap-3">
                <FileText
                  size={22}
                  className="text-indigo-600"
                />

                <h3 className="text-lg font-bold text-[#15182D]">
                  Full Transcript
                </h3>
              </div>

              {transcriptQuery.isPending ? (
                <div className="flex items-center gap-3 text-sm text-slate-500">
                  <LoaderCircle
                    size={19}
                    className="animate-spin"
                  />
                  Loading transcript...
                </div>
              ) : transcriptQuery.isError ? (
                <div className="text-sm text-red-600">
                  Could not load transcript.

                  <button
                    type="button"
                    onClick={() =>
                      void transcriptQuery.refetch()
                    }
                    className="ml-2 font-bold underline"
                  >
                    Retry
                  </button>
                </div>
              ) : (
                <div className="whitespace-pre-wrap rounded-2xl bg-[#F8F9FD] p-6 text-sm leading-8 text-slate-700">
                  {transcriptText ||
                    'No transcript text returned.'}
                </div>
              )}
            </div>
          ) : insightsQuery.isPending ? (
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <LoaderCircle
                size={19}
                className="animate-spin"
              />
              Loading AI insights...
            </div>
          ) : insightsQuery.isError ? (
            <div className="text-sm text-red-600">
              Could not load AI insights.

              <button
                type="button"
                onClick={() =>
                  void insightsQuery.refetch()
                }
                className="ml-2 font-bold underline"
              >
                Retry
              </button>
            </div>
          ) : activeTab === 'summary' ? (
            <div className="space-y-8">
              {/* SUMMARY */}
              <div>
                <div className="mb-4 flex items-center gap-3">
                  <Sparkles
                    size={21}
                    className="text-indigo-600"
                  />

                  <h3 className="text-lg font-bold text-[#15182D]">
                    Meeting Summary
                  </h3>
                </div>

                <div className="whitespace-pre-wrap text-sm leading-8 text-slate-700">
                  {renderValue(summary)}
                </div>
              </div>

              {/* KEY HIGHLIGHTS */}
              <div className="border-t border-slate-100 pt-7">
                <div className="mb-5 flex items-center gap-3">
                  <Lightbulb
                    size={21}
                    className="text-amber-500"
                  />

                  <h3 className="text-lg font-bold text-[#15182D]">
                    Key Highlights
                  </h3>
                </div>

                {renderValue(keyPoints)}
              </div>
            </div>
          ) : activeTab === 'actions' ? (
            <div>
              <div className="mb-5 flex items-center gap-3">
                <ListTodo
                  size={22}
                  className="text-indigo-600"
                />

                <h3 className="text-lg font-bold text-[#15182D]">
                  Action Items
                </h3>
              </div>

              {renderValue(actionItems)}
            </div>
          ) : (
            <div>
              <div className="mb-5 flex items-center gap-3">
                <Lightbulb
                  size={22}
                  className="text-indigo-600"
                />

                <h3 className="text-lg font-bold text-[#15182D]">
                  Key Decisions
                </h3>
              </div>

              {renderValue(decisions)}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

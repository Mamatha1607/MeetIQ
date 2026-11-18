
import { useEffect, useState } from 'react'
import { AudioLines, Sparkles } from 'lucide-react'

const prompts = [
  'Hey MeetIQ, can you summarize this meeting?',
  'Hey MeetIQ, can you transcribe this recording?',
  'Hey MeetIQ, can you find the action items?',
  'Hey MeetIQ, what decisions were made?',
]

export default function MeetIQTypewriter() {
  const [promptIndex, setPromptIndex] = useState(0)
  const [characterCount, setCharacterCount] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)
  const [reduceMotion, setReduceMotion] = useState(false)

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(media.matches)

    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (reduceMotion) return

    const prompt = prompts[promptIndex]
    let delay = isDeleting ? 28 : 55

    if (!isDeleting && characterCount === prompt.length) {
      delay = 1800
    } else if (isDeleting && characterCount === 0) {
      delay = 350
    }

    const timer = window.setTimeout(() => {
      if (!isDeleting && characterCount === prompt.length) {
        setIsDeleting(true)
      } else if (isDeleting && characterCount === 0) {
        setIsDeleting(false)
        setPromptIndex((index) => (index + 1) % prompts.length)
      } else {
        setCharacterCount((count) => count + (isDeleting ? -1 : 1))
      }
    }, delay)

    return () => window.clearTimeout(timer)
  }, [promptIndex, characterCount, isDeleting, reduceMotion])

  return (
    <div className="rounded-2xl border border-white/80 bg-white/95 px-5 py-4 shadow-lg shadow-indigo-950/10">
      <div className="mb-2 flex items-center gap-2 text-indigo-700">
        <Sparkles size={18} />
        <span className="text-sm font-bold">Ask MeetIQ</span>
      </div>

      <div className="flex min-h-[52px] items-center gap-3">
        <p className="flex-1 text-[15px] font-semibold leading-6 text-[#11152E]">
          {reduceMotion
            ? prompts[0]
            : prompts[promptIndex].slice(0, characterCount)}

          {!reduceMotion && (
            <span
              className="meetiq-typewriter-cursor"
              aria-hidden="true"
            >
              |
            </span>
          )}
        </p>

        <AudioLines
          size={22}
          className="shrink-0 text-indigo-600"
        />
      </div>

      <div className="mt-2 flex justify-center gap-2">
        {prompts.map((_, index) => (
          <span
            key={index}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index === (reduceMotion ? 0 : promptIndex)
                ? 'w-7 bg-indigo-600'
                : 'w-1.5 bg-indigo-200'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

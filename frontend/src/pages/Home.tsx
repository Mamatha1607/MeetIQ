
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  AudioLines,
  FileText,
  Sparkles,
  ListChecks,
  UploadCloud,
  BrainCircuit,
} from 'lucide-react'

import meetingTeam from '../assets/meeting-team.png'

const features = [
  {
    icon: AudioLines,
    title: 'Meeting Transcription',
    description:
      'Convert recorded conversations into readable transcripts.',
  },
  {
    icon: Sparkles,
    title: 'AI Summaries',
    description:
      'Turn long conversations into concise meeting summaries.',
  },
  {
    icon: ListChecks,
    title: 'Action Items',
    description:
      'Identify follow-up tasks and important next steps.',
  },
  {
    icon: FileText,
    title: 'Key Decisions',
    description:
      'Review important decisions discussed during meetings.',
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-[#F8F7FF]">
      

      {/* Hero */}
      <section className="mx-auto grid max-w-[1400px] items-center gap-12 px-6 py-16 lg:min-h-[650px] lg:grid-cols-2 lg:px-12">

        {/* Hero content */}
        <div className="meetiq-page-enter">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#ECE9FF] px-4 py-2 text-sm font-semibold text-indigo-700">
            <Sparkles size={16} />
            Your AI Meeting Assistant
          </div>

          <h1 className="max-w-[620px] text-4xl font-extrabold leading-[1.12] tracking-tight text-[#11152E] sm:text-5xl lg:text-[60px]">
            Every meeting.
            <br />
            <span className="text-indigo-600">
              More clarity.
            </span>
          </h1>

          <p className="mt-6 max-w-[540px] text-lg leading-8 text-slate-600">
            Turn meeting recordings into transcripts,
            meaningful summaries, important decisions,
            and actionable insights — all in one place.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/register"
              className="meetiq-gradient inline-flex items-center gap-3 rounded-xl px-7 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-200 transition hover:-translate-y-1"
            >
              Get Started
              <ArrowRight size={19} />
            </Link>

            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-white px-7 py-3.5 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50"
            >
              Explore Features
            </a>
          </div>

          <div className="mt-10 flex flex-wrap gap-5 text-sm text-slate-500">
            <span className="flex items-center gap-2">
              <UploadCloud size={17} className="text-indigo-600" />
              Upload recordings
            </span>

            <span className="flex items-center gap-2">
              <BrainCircuit size={17} className="text-indigo-600" />
              AI-powered insights
            </span>
          </div>
        </div>

        {/* Full meeting image, no cropping */}
        <div className="rounded-[28px] bg-gradient-to-br from-[#EAE5FF] to-[#DCD6FF] p-4 shadow-[0_25px_70px_rgba(79,70,229,0.12)]">
          <img
            src={meetingTeam}
            alt="Professionals collaborating during a meeting"
            className="block h-auto w-full rounded-2xl object-contain"
          />
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        className="scroll-mt-24 bg-white px-6 py-20 lg:px-12"
      >
        <div className="mx-auto max-w-[1250px]">

          <div className="mb-12 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest text-indigo-600">
              Features
            </p>

            <h2 className="text-3xl font-extrabold text-[#11152E] sm:text-4xl">
              Everything you need after a meeting
            </h2>

            <p className="mx-auto mt-4 max-w-[650px] text-slate-500">
              Spend less time reviewing recordings and more time
              focusing on what matters.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon

              return (
                <div
                  key={feature.title}
                  className="meetiq-card group p-6 transition-all duration-300 hover:-translate-y-2 hover:shadow-xl"
                >
                  <div className="mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-[#EEECFF] text-indigo-600 transition group-hover:bg-indigo-600 group-hover:text-white">
                    <Icon size={25} />
                  </div>

                  <h3 className="text-lg font-bold text-[#11152E]">
                    {feature.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-slate-500">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="scroll-mt-24 bg-[#F3F0FF] px-6 py-20 lg:px-12"
      >
        <div className="mx-auto max-w-[1100px] text-center">
          <p className="mb-3 text-sm font-bold uppercase tracking-widest text-indigo-600">
            How it works
          </p>

          <h2 className="text-3xl font-extrabold text-[#11152E] sm:text-4xl">
            From recording to insights
          </h2>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {[
              {
                number: '01',
                title: 'Upload',
                text: 'Upload your audio or video recording.',
              },
              {
                number: '02',
                title: 'Transcribe',
                text: 'MeetIQ converts speech into readable text.',
              },
              {
                number: '03',
                title: 'Review',
                text: 'Explore summaries, decisions, and action items.',
              },
            ].map((step) => (
              <div
                key={step.number}
                className="rounded-2xl border border-indigo-100 bg-white p-7 text-left shadow-sm"
              >
                <span className="text-3xl font-extrabold text-indigo-300">
                  {step.number}
                </span>

                <h3 className="mt-4 text-xl font-bold text-[#11152E]">
                  {step.title}
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  {step.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to action */}
      <section className="bg-white px-6 py-20 text-center">
        <h2 className="text-3xl font-extrabold text-[#11152E]">
          Ready to make meetings more useful?
        </h2>

        <p className="mt-4 text-slate-500">
          Start organizing your meeting conversations with MeetIQ.
        </p>

        <Link
          to="/register"
          className="meetiq-gradient mt-7 inline-flex items-center gap-2 rounded-xl px-7 py-3.5 text-sm font-bold text-white"
        >
          Create your account
          <ArrowRight size={18} />
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-indigo-100 bg-white px-6 py-7 text-center text-sm text-slate-400">
        MeetIQ · AI Meeting Intelligence
      </footer>
    </div>
  )
}

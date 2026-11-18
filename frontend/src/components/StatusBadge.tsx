import type { MeetingStatus } from '../types/meeting'
const styles: Record<MeetingStatus, string> = {created:'bg-slate-100 text-slate-600',uploaded:'bg-blue-50 text-blue-700',queued:'bg-amber-50 text-amber-700',processing:'bg-violet-50 text-violet-700',completed:'bg-emerald-50 text-emerald-700',failed:'bg-red-50 text-red-700'}
export default function StatusBadge({status}:{status:MeetingStatus}) { return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ${styles[status]}`}>{status}</span> }

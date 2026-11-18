export type MeetingStatus = 'created' | 'uploaded' | 'queued' | 'processing' | 'completed' | 'failed'
export interface Meeting {
  id: string
  title: string
  description: string | null
  status: MeetingStatus
  created_at: string
  updated_at: string
  processing_started_at: string | null
  processing_completed_at: string | null
  error_message: string | null
}
export interface Transcript { id?: string; meeting_id?: string; text?: string; language?: string | null; segments?: unknown[] }
export type Insights = Record<string, unknown>

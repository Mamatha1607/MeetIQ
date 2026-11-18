import { api } from './api'
import type { Meeting, Transcript, Insights } from '../types/meeting'
export const getMeetings = async (): Promise<Meeting[]> => (await api.get<Meeting[]>('/meetings/')).data
export const getMeeting = async (id: string): Promise<Meeting> => (await api.get<Meeting>(`/meetings/${id}`)).data
export interface CreateMeetingPayload { title: string; description?: string }
export const createMeeting = async (payload: CreateMeetingPayload): Promise<Meeting> => (await api.post<Meeting>('/meetings/', payload)).data
export interface UpdateMeetingPayload { title?: string; description?: string | null }
export const updateMeeting = async (id: string, payload: UpdateMeetingPayload): Promise<Meeting> => (await api.patch<Meeting>(`/meetings/${id}`, payload)).data
export const deleteMeeting = async (id: string): Promise<void> => { await api.delete(`/meetings/${id}`) }
export const processMeeting = async (id: string): Promise<void> => { await api.post(`/meetings/${id}/process`) }
export const uploadMeetingFile = async (id: string, file: File, onProgress?: (progress: number) => void): Promise<void> => {
  const data = new FormData(); data.append('file', file)
  await api.post(`/meetings/${id}/upload`, data, { timeout: 120000, onUploadProgress: event => { if (event.total) onProgress?.(Math.round(event.loaded / event.total * 100)) } })
}
export const getTranscript = async (id: string): Promise<Transcript> => (await api.get<Transcript>(`/meetings/${id}/transcript`)).data
export const getInsights = async (id: string): Promise<Insights> => (await api.get<Insights>(`/meetings/${id}/insights`)).data

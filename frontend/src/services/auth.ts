import { api } from './api'

export interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
}

export interface AuthCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function loginUser(credentials: AuthCredentials) {
  const response = await api.post<TokenResponse>(
    '/auth/login',
    credentials,
  )

  return response.data
}

export async function registerUser(credentials: AuthCredentials) {
  const response = await api.post<User>(
    '/auth/register',
    credentials,
  )

  return response.data
}

export async function getCurrentUser() {
  const response = await api.get<User>('/auth/me')
  return response.data
}
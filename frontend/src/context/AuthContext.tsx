import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  loginUser,
  registerUser,
  getCurrentUser,
  type AuthCredentials,
  type User,
} from '../services/auth'
import { setAccessToken } from '../services/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (credentials: AuthCredentials) => Promise<void>
  register: (credentials: AuthCredentials) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const queryClient = useQueryClient()

  const login = async (credentials: AuthCredentials) => {
    const tokenResponse = await loginUser(credentials)

    setAccessToken(tokenResponse.access_token)

    try {
      const currentUser = await getCurrentUser()
      queryClient.clear()
      setUser(currentUser)
    } catch (error) {
      setAccessToken(null)
      throw error
    }
  }

  const register = async (credentials: AuthCredentials) => {
    await registerUser(credentials)
    await login(credentials)
  }

  const logout = () => {
    setAccessToken(null)
    setUser(null)
    queryClient.clear()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}
import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { authApi } from '../services/authApi'
import { setApiAccessToken, setUnauthorizedHandler } from '../services/apiClient'

const STORAGE_KEY = 'content-reco-session'

const AuthContext = createContext(null)

const getInitials = (email) => {
  return email?.trim().slice(0, 1).toUpperCase() || '?'
}

const enrichUser = (user) => {
  return {
    ...user,
    initials: getInitials(user.email),
    name: user.username || user.email.split('@')[0],
  }
}

const readStoredUser = () => {
  try {
    const storedValue = window.localStorage.getItem(STORAGE_KEY)
    return storedValue ? JSON.parse(storedValue) : { accessToken: null, user: null }
  } catch {
    return { accessToken: null, user: null }
  }
}

export const AuthenticationProvider = ({ children }) => {
  const [session, setSession] = useState(readStoredUser)
  const [isLoading, setIsLoading] = useState(Boolean(session.accessToken))
  const [error, setError] = useState(null)
  const user = session.user ? enrichUser(session.user) : null

  const clearSession = useCallback(() => {
    setApiAccessToken(null)
    setSession({ accessToken: null, user: null })
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => clearSession())
    return () => setUnauthorizedHandler(null)
  }, [clearSession])

  useEffect(() => {
    setApiAccessToken(session.accessToken)

    if (session.accessToken && session.user) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
      return
    }

    window.localStorage.removeItem(STORAGE_KEY)
  }, [session])

  useEffect(() => {
    let isActive = true

    const refreshSession = async () => {
      if (!session.accessToken) {
        return
      }

      try {
        const currentUser = await authApi.getCurrentUser()

        if (isActive) {
          setSession((currentSession) => ({
            ...currentSession,
            user: currentUser,
          }))
        }
      } catch (refreshError) {
        if (isActive) {
          clearSession()
          setError(refreshError.message)
        }
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    refreshSession()

    return () => {
      isActive = false
    }
  }, [clearSession, session.accessToken])

  const signIn = useCallback(async ({ email, password }) => {
    setError(null)
    setIsLoading(true)

    try {
      const nextSession = await authApi.login({ email, password })
      setApiAccessToken(nextSession.accessToken)
      setSession(nextSession)
      return nextSession.user
    } catch (signInError) {
      setError(signInError.message)
      throw signInError
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signUp = useCallback(async ({ email, password, username }) => {
    setError(null)
    setIsLoading(true)

    try {
      const nextSession = await authApi.register({ email, password, username })
      setApiAccessToken(nextSession.accessToken)
      setSession(nextSession)
      return nextSession.user
    } catch (signUpError) {
      setError(signUpError.message)
      throw signUpError
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signOut = useCallback(() => {
    setError(null)
    clearSession()
  }, [clearSession])

  const updateCurrentUser = useCallback((nextUser) => {
    setSession((currentSession) => ({
      ...currentSession,
      user: nextUser,
    }))
  }, [])

  const value = useMemo(
    () => ({
      error,
      isAuthenticated: Boolean(user),
      isLoading,
      signIn,
      signOut,
      signUp,
      updateCurrentUser,
      user,
    }),
    [error, isLoading, signIn, signOut, signUp, updateCurrentUser, user],
  )

  return createElement(AuthContext, { value }, children)
}

export const useAuth = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthenticationProvider')
  }

  return context
}

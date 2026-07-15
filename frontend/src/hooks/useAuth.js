import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

const STORAGE_KEY = 'tonights-pick-session'

const AuthContext = createContext(null)

const getInitials = (email) => {
  return email?.trim().slice(0, 1).toUpperCase() || '?'
}

const readStoredUser = () => {
  try {
    const storedValue = window.localStorage.getItem(STORAGE_KEY)
    return storedValue ? JSON.parse(storedValue) : null
  } catch {
    return null
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(readStoredUser)

  useEffect(() => {
    if (user) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
      return
    }

    window.localStorage.removeItem(STORAGE_KEY)
  }, [user])

  const signIn = useCallback(({ email }) => {
    const nextUser = {
      email,
      id: 1,
      initials: getInitials(email),
      name: email.split('@')[0],
    }

    setUser(nextUser)
    return nextUser
  }, [])

  const signOut = useCallback(() => {
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(user),
      signIn,
      signOut,
      user,
    }),
    [signIn, signOut, user],
  )

  return createElement(AuthContext, { value }, children)
}

export const useAuth = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}

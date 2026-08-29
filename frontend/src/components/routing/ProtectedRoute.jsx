import { Navigate, useLocation } from 'react-router-dom'
import { LoadingState } from '../ui'
import { useAuth } from '../../hooks'

const ProtectedRoute = ({ children }) => {
  const location = useLocation()
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <section className="page page--centered">
        <LoadingState title="Session en cours de vérification" />
      </section>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}

export default ProtectedRoute

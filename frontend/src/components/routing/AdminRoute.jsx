import { Navigate } from 'react-router-dom'
import { LoadingState } from '../ui'
import { useAuth } from '../../hooks'

const AdminRoute = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <section className="page page--centered">
        <LoadingState title="Vérification des autorisations" />
      </section>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== 'ADMIN') {
    return <Navigate to="/discover" replace />
  }

  return children
}

export default AdminRoute

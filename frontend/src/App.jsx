import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import ProtectedRoute from './components/routing/ProtectedRoute'
import AdminRoute from './components/routing/AdminRoute'
import { NAV_ITEMS } from './data/navigation'
import { useAuth } from './hooks'
import DevPage from './pages/DevPage'
import DiscoveryPage from './pages/DiscoveryPage'
import HomePage from './pages/HomePage'
import PreferencesPage from './pages/PreferencesPage'
import ProfilePage from './pages/ProfilePage'
import SignInPage from './pages/SignInPage'

const App = () => {
  const { isAuthenticated, user } = useAuth()

  return (
    <AppShell
      navItems={NAV_ITEMS}
      user={user}
    >
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/discover" replace /> : <SignInPage />}
        />
        <Route
          path="/preferences"
          element={
            <ProtectedRoute>
              <PreferencesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/discover"
          element={
            <ProtectedRoute>
              <DiscoveryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dev"
          element={
            <AdminRoute>
              <DevPage />
            </AdminRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export default App

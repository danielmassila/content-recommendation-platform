import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import { NAV_ITEMS } from './data/navigation'
import DiscoveryPage from './pages/DiscoveryPage'
import HomePage from './pages/HomePage'
import PreferencesPage from './pages/PreferencesPage'
import ProfilePage from './pages/ProfilePage'
import SignInPage from './pages/SignInPage'

const App = () => {
  return (
    <AppShell
      navItems={NAV_ITEMS}
      user={{ name: 'Daniel', initials: 'D' }}
    >
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<SignInPage />} />
        <Route path="/preferences" element={<PreferencesPage />} />
        <Route path="/discover" element={<DiscoveryPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export default App

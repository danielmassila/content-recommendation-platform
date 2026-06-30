import AppShell from './components/layout/AppShell'
import { NAV_ITEMS } from './data/navigation'
import { useAppNavigation } from './hooks/useAppNavigation'
import DiscoveryPage from './pages/DiscoveryPage'
import HomePage from './pages/HomePage'
import PreferencesPage from './pages/PreferencesPage'
import ProfilePage from './pages/ProfilePage'
import SignInPage from './pages/SignInPage'

const pages = {
  home: HomePage,
  signIn: SignInPage,
  preferences: PreferencesPage,
  discovery: DiscoveryPage,
  profile: ProfilePage,
}

const App = () => {
  const navigation = useAppNavigation('home')
  const ActivePage = pages[navigation.currentPage]

  return (
    <AppShell
      currentPage={navigation.currentPage}
      navItems={NAV_ITEMS}
      onNavigate={navigation.goTo}
      user={{ name: 'Daniel', initials: 'D' }}
    >
      <ActivePage onNavigate={navigation.goTo} />
    </AppShell>
  )
}

export default App

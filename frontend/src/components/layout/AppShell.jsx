import { Link, NavLink } from 'react-router-dom'
import Button from '../ui/Button'
import { useAuth } from '../../hooks'

const AppShell = ({ children, navItems, user }) => {
  const { signOut } = useAuth()

  return (
    <div className="app-shell">
      <div className="void-backdrop" aria-hidden="true">
        <span className="void-backdrop__axis void-backdrop__axis--left" />
        <span className="void-backdrop__axis void-backdrop__axis--right" />
      </div>
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand__mark">TP</span>
          <span>Tonight&apos;s Pick</span>
        </Link>

        {user ? (
          <nav className="main-nav" aria-label="Navigation principale">
            {navItems.map((item) => (
              <NavLink
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`.trim()}
                key={item.id}
                to={item.path}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        ) : (
          <div aria-hidden="true" />
        )}

        {user ? (
          <div className="user-menu" aria-label="Utilisateur connecté">
            <span className="avatar" aria-hidden="true">
              {user.initials}
            </span>
            <span>{user.name}</span>
            <Button variant="ghost" onClick={signOut}>
              Déconnexion
            </Button>
          </div>
        ) : (
          <div className="user-menu" aria-label="Utilisateur non connecté">
            <Button as={Link} to="/login" variant="ghost">
              Connexion
            </Button>
          </div>
        )}
      </header>

      <main className="app-main">{children}</main>
    </div>
  )
}

export default AppShell

import { Link, NavLink } from 'react-router-dom'
import Button from '../ui/Button'

const AppShell = ({ children, navItems, user }) => {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">
          Tonight&apos;s Pick
        </Link>

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

        <div className="user-menu" aria-label="Utilisateur connecté">
          <span className="avatar" aria-hidden="true">
            {user.initials}
          </span>
          <span>{user.name}</span>
          <Button as={Link} to="/login" variant="ghost">
            Connexion
          </Button>
        </div>
      </header>

      <main>{children}</main>
    </div>
  )
}

export default AppShell

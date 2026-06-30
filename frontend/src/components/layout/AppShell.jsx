import Button from '../ui/Button'

const AppShell = ({ children, currentPage, navItems, onNavigate, user }) => {
  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" type="button" onClick={() => onNavigate('home')}>
          Tonight&apos;s Pick
        </button>

        <nav className="main-nav" aria-label="Navigation principale">
          {navItems.map((item) => (
            <button
              aria-current={currentPage === item.id ? 'page' : undefined}
              className="nav-link"
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="user-menu" aria-label="Utilisateur connecté">
          <span className="avatar" aria-hidden="true">
            {user.initials}
          </span>
          <span>{user.name}</span>
          <Button variant="ghost" onClick={() => onNavigate('signIn')}>
            Connexion
          </Button>
        </div>
      </header>

      <main>{children}</main>
    </div>
  )
}

export default AppShell

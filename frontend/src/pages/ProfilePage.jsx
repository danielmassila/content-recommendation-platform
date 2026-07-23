import { useState } from 'react'
import { Button, EmptyState, ErrorState, LoadingState, TextField } from '../components/ui'
import { useAuth, useUserProfile } from '../hooks'
import { usersApi } from '../services'

const AccountSettings = ({ onUserUpdate, user }) => {
  const [accountForm, setAccountForm] = useState({
    email: user.email ?? '',
    username: user.username ?? '',
  })
  const [accountMessage, setAccountMessage] = useState('')
  const [accountError, setAccountError] = useState('')
  const [isAccountSaving, setIsAccountSaving] = useState(false)
  const [passwordForm, setPasswordForm] = useState({ currentPassword: '', newPassword: '' })
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [isPasswordSaving, setIsPasswordSaving] = useState(false)

  const handleAccountSubmit = async (event) => {
    event.preventDefault()
    setAccountError('')
    setAccountMessage('')
    setIsAccountSaving(true)

    try {
      const updatedUser = await usersApi.updateUser(user.id, accountForm)
      onUserUpdate(updatedUser)
      setAccountMessage('Profil mis à jour.')
    } catch (caughtError) {
      setAccountError(caughtError.message)
    } finally {
      setIsAccountSaving(false)
    }
  }

  const handlePasswordSubmit = async (event) => {
    event.preventDefault()
    setPasswordError('')
    setPasswordMessage('')
    setIsPasswordSaving(true)

    try {
      await usersApi.changePassword(user.id, passwordForm)
      setPasswordForm({ currentPassword: '', newPassword: '' })
      setPasswordMessage('Mot de passe mis à jour.')
    } catch (caughtError) {
      setPasswordError(caughtError.message)
    } finally {
      setIsPasswordSaving(false)
    }
  }

  return (
    <section className="account-settings" aria-label="Paramètres du compte">
      <form className="settings-card" onSubmit={handleAccountSubmit}>
        <div>
          <h2>Informations du compte</h2>
          <p>Modifie ton nom d’utilisateur ou ton email.</p>
        </div>
        <TextField
          autoComplete="username"
          id="profile-username"
          label="Nom d’utilisateur"
          minLength="2"
          onChange={(event) => setAccountForm((form) => ({ ...form, username: event.target.value }))}
          required
          type="text"
          value={accountForm.username}
        />
        <TextField
          autoComplete="email"
          id="profile-email"
          label="Email"
          onChange={(event) => setAccountForm((form) => ({ ...form, email: event.target.value }))}
          required
          type="email"
          value={accountForm.email}
        />
        {accountError ? <p className="form-error">{accountError}</p> : null}
        {accountMessage ? <p className="form-success">{accountMessage}</p> : null}
        <Button disabled={isAccountSaving} type="submit">
          {isAccountSaving ? 'Sauvegarde...' : 'Sauvegarder'}
        </Button>
      </form>

      <form className="settings-card" onSubmit={handlePasswordSubmit}>
        <div>
          <h2>Mot de passe</h2>
          <p>Choisis un nouveau mot de passe à partir de l’ancien.</p>
        </div>
        <TextField
          autoComplete="current-password"
          id="current-password"
          label="Mot de passe actuel"
          onChange={(event) => setPasswordForm((form) => ({ ...form, currentPassword: event.target.value }))}
          required
          type="password"
          value={passwordForm.currentPassword}
        />
        <TextField
          autoComplete="new-password"
          id="new-password"
          label="Nouveau mot de passe"
          minLength="8"
          onChange={(event) => setPasswordForm((form) => ({ ...form, newPassword: event.target.value }))}
          required
          type="password"
          value={passwordForm.newPassword}
        />
        {passwordError ? <p className="form-error">{passwordError}</p> : null}
        {passwordMessage ? <p className="form-success">{passwordMessage}</p> : null}
        <Button disabled={isPasswordSaving} type="submit">
          {isPasswordSaving ? 'Sauvegarde...' : 'Changer le mot de passe'}
        </Button>
      </form>
    </section>
  )
}

const ProfilePage = () => {
  const { updateCurrentUser, user: currentUser } = useAuth()
  const { error, initials, isEmpty, isLoading, ratedMovieRows, refresh, stats, user } =
    useUserProfile(currentUser?.id)

  const handleUserUpdate = (updatedUser) => {
    updateCurrentUser(updatedUser)
    refresh()
  }

  return (
    <section className="page page--profile">
      <aside className="profile-card">
        <span className="profile-avatar">{initials}</span>
        <h1>{user?.username ?? currentUser?.name ?? 'Utilisateur'}</h1>
        <p>{user?.email ?? `Compte #${currentUser?.id}`}</p>
        <section className="profile-algo-card">
          <h2>Algo utilisé</h2>
          <strong>hybrid_usercf_pop</strong>
          <p>
            Mélange entre popularité pondérée et similarité entre utilisateurs. Les prochaines notes rendront le profil
            plus précis.
          </p>
        </section>
      </aside>

      <div className="profile-content">
        {isLoading ? <LoadingState title="Chargement du profil..." /> : null}

        {error ? (
          <ErrorState
            error={error}
            eyebrow="Profil indisponible"
            onRetry={refresh}
            title="Impossible de charger le profil"
          />
        ) : null}

        <div className="stats-grid">
          {stats.map((stat) => (
            <article className="stat-card" key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>

        {!isLoading && !error && user ? (
          <AccountSettings key={`${user.id}-${user.email}-${user.username}`} onUserUpdate={handleUserUpdate} user={user} />
        ) : null}

        {isEmpty ? <EmptyState title="Aucune note récente pour ce compte" /> : null}

        {!isLoading && !error ? (
          <details className="rating-history" open>
            <summary>
              <span>Notes récentes</span>
              <strong>{ratedMovieRows[0]?.items.length ?? 0}</strong>
            </summary>
            <div className="rating-history__list">
              {ratedMovieRows[0]?.items.map((movie) => {
                const rating = Number(movie.rating?.rating ?? 0)
                return (
                  <article className="rating-history__item" key={movie.id}>
                    <div>
                      <h3>{movie.title}</h3>
                      <p>{movie.year} · {movie.genres.join(' / ')}</p>
                    </div>
                    <div className="rating-meter" aria-label={`Note ${rating} sur 5`}>
                      <span style={{ width: `${(rating / 5) * 100}%` }} />
                    </div>
                    <strong>{rating}/5</strong>
                  </article>
                )
              })}
            </div>
          </details>
        ) : null}
      </div>
    </section>
  )
}

export default ProfilePage

import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button, TextField } from '../components/ui'
import { useAuth } from '../hooks'

const SignInPage = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { error: authError, isLoading, signIn, signUp } = useAuth()
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('daniel@example.fr')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState(null)

  const isRegisterMode = mode === 'register'
  const redirectPath = location.state?.from?.pathname ?? '/discover'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setFormError(null)

    try {
      const authAction = isRegisterMode ? signUp : signIn
      await authAction({ email, password })
      navigate(redirectPath, { replace: true })
    } catch (error) {
      setFormError(error.message)
    }
  }

  return (
    <section className="page page--centered">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-card__header">
          <h1>{isRegisterMode ? 'Créer un compte' : 'Connexion'}</h1>
          <div className="auth-card__switcher" aria-label="Mode authentification">
            <button
              aria-pressed={!isRegisterMode}
              className="auth-card__switch"
              onClick={() => setMode('login')}
              type="button"
            >
              Connexion
            </button>
            <button
              aria-pressed={isRegisterMode}
              className="auth-card__switch"
              onClick={() => setMode('register')}
              type="button"
            >
              Inscription
            </button>
          </div>
        </div>
        <TextField
          autoComplete="email"
          id="email"
          label="Email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="daniel@example.fr"
          type="email"
          value={email}
        />
        <TextField
          autoComplete="current-password"
          id="password"
          label="Mot de passe"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
          type="password"
          value={password}
        />
        {(formError || authError) && (
          <p className="form-error" role="alert">
            {formError || authError}
          </p>
        )}
        <Button className="auth-card__submit" disabled={isLoading} type="submit">
          {isLoading ? 'Chargement...' : isRegisterMode ? 'Créer le compte' : 'Se connecter'}
        </Button>
      </form>
    </section>
  )
}

export default SignInPage

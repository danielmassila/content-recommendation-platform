import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, TextField } from '../components/ui'
import { useAuth } from '../hooks'

const SignInPage = () => {
  const navigate = useNavigate()
  const { signIn } = useAuth()
  const [email, setEmail] = useState('daniel@example.fr')
  const [password, setPassword] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    signIn({ email, password })
    navigate('/discover')
  }

  return (
    <section className="page page--centered">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Connexion</h1>
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
        <Button className="auth-card__submit">Se connecter</Button>
        <p className="auth-card__hint">
          Connexion temporaire côté front. Le backend auth pourra remplacer ce flux plus tard.
        </p>
        <button className="text-button" type="button">
          Mot de passe oublié
        </button>
      </form>
    </section>
  )
}

export default SignInPage

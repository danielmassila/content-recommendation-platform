import { Button, TextField } from '../components/ui'

const SignInPage = () => {
  return (
    <section className="page page--centered">
      <form className="auth-card">
        <h1>Connexion</h1>
        <TextField
          autoComplete="email"
          id="email"
          label="Email"
          placeholder="daniel@example.fr"
          type="email"
        />
        <TextField
          autoComplete="current-password"
          id="password"
          label="Mot de passe"
          placeholder="••••••••"
          type="password"
        />
        {/* TODO auth: brancher Spring Security / JWT et gérer les états erreur + chargement. */}
        <Button className="auth-card__submit">Se connecter</Button>
        <button className="text-button" type="button">
          Mot de passe oublié
        </button>
      </form>
    </section>
  )
}

export default SignInPage

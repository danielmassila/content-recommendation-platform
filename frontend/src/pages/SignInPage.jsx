import Button from '../components/ui/Button'

const SignInPage = () => {
  return (
    <section className="page page--centered">
      <form className="auth-card">
        <h1>Connexion</h1>
        <label>
          Email
          <input autoComplete="email" placeholder="daniel@example.fr" type="email" />
        </label>
        <label>
          Mot de passe
          <input autoComplete="current-password" placeholder="••••••••" type="password" />
        </label>
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

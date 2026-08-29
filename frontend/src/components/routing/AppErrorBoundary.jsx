import { Component } from 'react'
import { Button } from '../ui'

class AppErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  handleReset = () => {
    this.setState({ error: null })
    window.location.assign('/')
  }

  render() {
    if (!this.state.error) {
      return this.props.children
    }

    return (
      <main className="page page--centered" role="alert">
        <section className="feedback-state">
          <p className="eyebrow">Erreur inattendue</p>
          <h1>L’application ne peut pas afficher cette page</h1>
          <p>Recharge la page. Si le problème persiste, réessaie dans quelques instants.</p>
          <Button onClick={this.handleReset}>Retour à l’accueil</Button>
        </section>
      </main>
    )
  }
}

export default AppErrorBoundary

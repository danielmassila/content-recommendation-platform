import { useState } from 'react'
import { Button, ErrorState } from '../components/ui'
import { recommendationsApi } from '../services'

const DevPage = () => {
  const [error, setError] = useState(null)
  const [isRecomputing, setIsRecomputing] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  const handleRecomputeAll = async () => {
    setError(null)
    setSuccessMessage('')
    setIsRecomputing(true)

    try {
      await recommendationsApi.recomputeAllRecommendations()
      setSuccessMessage('Recalcul global lancé. Les recommandations seront mises à jour après la fin du job.')
    } catch (caughtError) {
      setError(caughtError)
    } finally {
      setIsRecomputing(false)
    }
  }

  return (
    <section className="page page--dev">
      <div className="dev-panel">
        <p className="eyebrow">Outils dev</p>
        <h1>Recalcul des recommandations</h1>
        <p>
          Lance un recalcul global quand les notes, les préférences ou les métadonnées ont changé. Cette action peut
          prendre un peu de temps selon la taille du dataset.
        </p>

        {error ? (
          <ErrorState
            error={error}
            eyebrow="Job indisponible"
            onRetry={handleRecomputeAll}
            title="Impossible de lancer le recalcul"
          />
        ) : null}

        {successMessage ? (
          <p className="form-success" role="status">
            {successMessage}
          </p>
        ) : null}

        <div className="dev-actions">
          <Button disabled={isRecomputing} onClick={handleRecomputeAll}>
            {isRecomputing ? 'Recalcul en cours...' : 'Relancer le calcul global'}
          </Button>
        </div>
      </div>
    </section>
  )
}

export default DevPage

import FeedbackState from './FeedbackState'

const ErrorState = ({
  actionLabel = 'Réessayer',
  eyebrow = 'Erreur',
  error,
  message,
  onRetry,
  title = 'Impossible de charger les données',
}) => {
  return (
    <FeedbackState
      actionLabel={onRetry ? actionLabel : undefined}
      eyebrow={eyebrow}
      message={message ?? error?.message}
      onAction={onRetry}
      title={title}
    />
  )
}

export default ErrorState

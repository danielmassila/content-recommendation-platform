import FeedbackState from './FeedbackState'

const LoadingState = ({ title = 'Chargement...', message }) => {
  return <FeedbackState eyebrow="Chargement" message={message} title={title} />
}

export default LoadingState

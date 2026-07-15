import FeedbackState from './FeedbackState'

const EmptyState = ({ eyebrow = 'Aucun résultat', message, title }) => {
  return <FeedbackState eyebrow={eyebrow} message={message} title={title} />
}

export default EmptyState

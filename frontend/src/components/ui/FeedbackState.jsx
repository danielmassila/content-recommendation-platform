import Button from './Button'

const FeedbackState = ({ actionLabel, eyebrow, message, onAction, title }) => {
  return (
    <section className="feedback-panel">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {message ? <p>{message}</p> : null}
      {actionLabel && onAction ? <Button onClick={onAction}>{actionLabel}</Button> : null}
    </section>
  )
}

export default FeedbackState

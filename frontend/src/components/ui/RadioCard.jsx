const RadioCard = ({ hint, label, name, value, ...inputProps }) => {
  return (
    <label className="radio-card">
      <input name={name} type="radio" value={value} {...inputProps} />
      <span>{label}</span>
      {hint ? <small>{hint}</small> : null}
    </label>
  )
}

export default RadioCard

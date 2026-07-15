const TextField = ({ id, label, ...inputProps }) => {
  return (
    <label className="field" htmlFor={id}>
      {label}
      <input id={id} {...inputProps} />
    </label>
  )
}

export default TextField

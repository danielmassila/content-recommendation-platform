const SelectField = ({ children, id, label, ...selectProps }) => {
  return (
    <label className="field select-field" htmlFor={id}>
      {label}
      <select id={id} {...selectProps}>
        {children}
      </select>
    </label>
  )
}

export default SelectField

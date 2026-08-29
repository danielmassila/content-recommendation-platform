const Button = ({ children, className = '', variant = 'primary', ...props }) => {
  const Component = props.as ?? 'button'
  const componentProps = { ...props }
  delete componentProps.as

  return (
    <Component
      className={`button button--${variant} ${className}`.trim()}
      type={Component === 'button' ? 'button' : undefined}
      {...componentProps}
    >
      {children}
    </Component>
  )
}

export default Button

import { useTransition } from './context'

export function TransitionLink({ to, children, onClick, ...rest }) {
  const { navigate } = useTransition()
  const href = typeof to === 'string' ? to : '/'
  return (
    <a
      href={href}
      onClick={(e) => {
        e.preventDefault()
        if (onClick) onClick(e)
        navigate(to)
      }}
      {...rest}
    >
      {children}
    </a>
  )
}

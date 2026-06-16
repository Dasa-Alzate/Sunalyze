import { useTransition } from './context'

export function TransitionLink({ to, children, onClick, ...rest }) {
  const { navigate } = useTransition()
  return (
    <a
      href={typeof to === 'string' ? to : '#'}
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

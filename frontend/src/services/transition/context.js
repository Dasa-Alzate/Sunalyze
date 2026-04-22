import { createContext, useContext } from 'react'

export const TransitionContext = createContext({
  navigate: () => {},
  phase: 'idle',
  busy: false,
})

export function useTransition() {
  return useContext(TransitionContext)
}

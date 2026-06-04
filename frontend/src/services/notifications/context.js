import { createContext, useContext } from 'react'

export const NotificationsContext = createContext({
  count: 0,
  items: [],
  page: 1,
  hasMore: false,
  loading: false,
  error: null,
  open: false,
  setOpen: () => {},
  loadFirst: () => {},
  loadMore: () => {},
  markRead: () => {},
  readAll: () => {},
})

export function useNotifications() {
  return useContext(NotificationsContext)
}

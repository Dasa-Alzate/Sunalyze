import { createContext, useContext } from 'react'

export const CommandContext = createContext({
  openPalette: () => {},
  closePalette: () => {},
  openSheet: () => {},
  closeSheet: () => {},
  runAction: () => {},
  paletteOpen: false,
  sheetOpen: false,
})

export function useCommands() {
  return useContext(CommandContext)
}
